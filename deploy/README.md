# Deploy Mini Shop to AWS ECS (EC2 launch type) + RDS Postgres

Region: `ap-south-1` (Mumbai). Plan: 1 × `t3.micro` EC2 instance in a **public subnet**, no load balancer, no NAT Gateway (cheapest setup for learning).

```
Your laptop --HTTP :8000-->  EC2 instance (ECS agent)  --5432, SSL-->  RDS Postgres
                             └─ container "web" (gunicorn + Django)
```

Replace these placeholders everywhere below and in `deploy/task-definition.json`:

| Placeholder | Where to find it |
|---|---|
| `<ACCOUNT_ID>` | Top-right menu in the AWS console (12 digits) |
| `<RDS_ENDPOINT>` | RDS → your database → *Connectivity & security* → Endpoint |
| `<RDS_MASTER_USERNAME>` | RDS → your database → *Configuration* → Master username |
| `<EC2_PUBLIC_IP>` | Step 6, after the instance starts |

You need on your laptop: AWS CLI v2 (`aws configure`, region `ap-south-1`) and Docker.

---

## 1. Check the RDS side

1. **Database name.** The app uses a database called `minishop`. If you didn't set "Initial database name" when creating RDS, it only has `postgres`. Either set `POSTGRES_DB` to `postgres`, or create `minishop` later (Step 8 shows how).
2. **Security group.** RDS must accept port 5432 **from the ECS instance's security group** (not from 0.0.0.0/0). You'll add this rule in Step 6, once that group exists.
3. **SSL.** RDS Postgres 15+ forces SSL. The task definition sets `DB_SSLMODE=require`, so that's already handled.

## 2. Push the image to ECR

```bash
aws ecr create-repository --repository-name minishop --region ap-south-1

aws ecr get-login-password --region ap-south-1 \
  | docker login --username AWS --password-stdin <ACCOUNT_ID>.dkr.ecr.ap-south-1.amazonaws.com

# --platform: t3.micro is x86. Without this, an Apple Silicon Mac would build an ARM image that won't start.
docker build --platform linux/amd64 -t minishop .
docker tag minishop:latest <ACCOUNT_ID>.dkr.ecr.ap-south-1.amazonaws.com/minishop:latest
docker push <ACCOUNT_ID>.dkr.ecr.ap-south-1.amazonaws.com/minishop:latest
```

## 3. Store the secrets (never put passwords in the task definition)

```bash
aws ssm put-parameter --region ap-south-1 --type SecureString \
  --name /minishop/POSTGRES_PASSWORD --value '<your RDS master password>'

aws ssm put-parameter --region ap-south-1 --type SecureString \
  --name /minishop/DJANGO_SECRET_KEY \
  --value "$(python3 -c 'import secrets; print(secrets.token_urlsafe(50))')"
```

## 4. Execution role (lets ECS pull the image, read secrets, write logs)

IAM → Roles → check whether `ecsTaskExecutionRole` exists. If not: *Create role* → trusted entity **Elastic Container Service Task** → attach `AmazonECSTaskExecutionRolePolicy`.

Then add an inline policy so it can read the two parameters:

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": "ssm:GetParameters",
    "Resource": "arn:aws:ssm:ap-south-1:<ACCOUNT_ID>:parameter/minishop/*"
  }]
}
```

## 5. Log group

```bash
aws logs create-log-group --log-group-name /ecs/minishop --region ap-south-1
aws logs put-retention-policy --log-group-name /ecs/minishop --retention-in-days 7 --region ap-south-1
```

## 6. ECS cluster with one EC2 instance

Console → ECS → *Create cluster*:
- Name: `minishop`
- Infrastructure: **Amazon EC2 instances** (untick Fargate)
- Auto Scaling group: create new, **Amazon Linux 2023 (ECS optimized)**, instance type `t3.micro`, desired/min/max = **1**
- Network: your default VPC, a **public** subnet, *Auto-assign public IP*: **Turn on**
- Security group: create new, e.g. `minishop-ecs`, inbound **TCP 8000 from My IP**

Then:
- **RDS security group** → *Inbound rules* → add **PostgreSQL 5432**, source = the `minishop-ecs` security group.
- EC2 → Instances → copy the instance's **Public IPv4 address**. That's `<EC2_PUBLIC_IP>`.

## 7. Register the task definition

Fill in the placeholders in `deploy/task-definition.json`, then:

```bash
aws ecs register-task-definition --cli-input-json file://deploy/task-definition.json --region ap-south-1
```

## 8. Run migrations once (a one-off task)

```bash
aws ecs run-task --cluster minishop --task-definition minishop --launch-type EC2 --region ap-south-1 \
  --overrides '{"containerOverrides":[{"name":"web","command":["python","manage.py","migrate"]}]}'
```

Check the result in CloudWatch → Log groups → `/ecs/minishop`. You should see `Applying catalog.0001_initial... OK` and so on.

If Postgres says `database "minishop" does not exist`, create it with a one-off task (it connects to the default `postgres` database):

```bash
aws ecs run-task --cluster minishop --task-definition minishop --launch-type EC2 --region ap-south-1 \
  --overrides '{"containerOverrides":[{"name":"web","environment":[{"name":"POSTGRES_DB","value":"postgres"}],"command":["python","-c","import django,os;os.environ.setdefault(\"DJANGO_SETTINGS_MODULE\",\"config.settings\");django.setup();from django.db import connection;connection.ensure_connection();connection.connection.autocommit=True;connection.cursor().execute(\"CREATE DATABASE minishop\");print(\"created\")"]}]}'
```

Then run the migrate task again.

Optional admin user:

```bash
aws ecs run-task --cluster minishop --task-definition minishop --launch-type EC2 --region ap-south-1 \
  --overrides '{"containerOverrides":[{"name":"web","environment":[{"name":"DJANGO_SUPERUSER_EMAIL","value":"you@example.com"},{"name":"DJANGO_SUPERUSER_PASSWORD","value":"<pick one>"}],"command":["python","manage.py","createsuperuser","--noinput"]}]}'
```

## 9. Start the service

```bash
aws ecs create-service --cluster minishop --service-name minishop-web \
  --task-definition minishop --desired-count 1 --launch-type EC2 --region ap-south-1
```

## 10. Check it works

```bash
curl http://<EC2_PUBLIC_IP>:8000/health/        # {"status": "ok"}
curl http://<EC2_PUBLIC_IP>:8000/health/db/     # {"status": "ok", "db": "ok", "db_connections": N}
curl http://<EC2_PUBLIC_IP>:8000/api/v1/products/
```

| Problem | Likely cause |
|---|---|
| `curl` hangs | Instance security group doesn't allow 8000 from your IP, or the instance has no public IP |
| `/health/` OK, `/health/db/` shows `timeout` | RDS security group doesn't allow 5432 from `minishop-ecs` |
| `/health/db/` shows `password authentication failed` | Wrong value in `/minishop/POSTGRES_PASSWORD` or wrong username |
| `/health/db/` shows `no pg_hba.conf entry ... no encryption` | `DB_SSLMODE` is not `require` |
| API returns 400 | `DJANGO_ALLOWED_HOSTS` doesn't contain the IP you're calling |
| Task stops right away | CloudWatch logs; often a missing env var or the secret can't be read (Step 4) |

---

## Phase 6: connection-pooling experiments on AWS

Change **only env values** in the task definition, register it again (Step 7), then roll the service:

```bash
aws ecs update-service --cluster minishop --service minishop-web \
  --task-definition minishop --force-new-deployment --region ap-south-1
```

| Experiment | Env values |
|---|---|
| 6-1 No pooling | `DB_CONN_MAX_AGE=0`, `DB_POOL=False` |
| 6-2 Persistent | `DB_CONN_MAX_AGE=60`, `DB_POOL=False` |
| 6-3 Django pool | `DB_POOL=True`, `DB_POOL_MAX=4`, try `GUNICORN_THREADS=4` |

For each one, run the load test from your laptop and read the connection count **while it runs**:

```bash
# (set DISABLE_THROTTLE=True in the task definition for load tests)
hey -n 2000 -c 50 http://<EC2_PUBLIC_IP>:8000/api/v1/products/
curl http://<EC2_PUBLIC_IP>:8000/health/db/      # in a second terminal, during the test
```

RDS → your DB → *Monitoring* → **DatabaseConnections** shows the same thing as a graph.

**Maximum connections from one task** = `GUNICORN_WORKERS × GUNICORN_THREADS` (CONN_MAX_AGE mode) or `GUNICORN_WORKERS × DB_POOL_MAX` (pool mode). Multiply by the number of tasks and keep the total under RDS `max_connections` (about 80 on a `db.t3.micro`, which has 1 GB RAM).

## Stop paying when you're done

```bash
aws ecs update-service --cluster minishop --service minishop-web --desired-count 0 --region ap-south-1
```

Then set the cluster's Auto Scaling group to 0 instances (EC2 → Auto Scaling groups), and stop or delete the RDS instance if you don't need it. RDS and EC2 bill by the hour while running.
