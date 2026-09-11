resource "aws_ecs_cluster" "qa" {
  name = local.name_prefix

  setting {
    name  = "containerInsights"
    value = "enabled"
  }
}

resource "aws_ecs_task_definition" "qa" {
  family                   = local.name_prefix
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = tostring(var.task_cpu)
  memory                   = tostring(var.task_memory)
  execution_role_arn       = aws_iam_role.ecs_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn

  runtime_platform {
    operating_system_family = "LINUX"
    cpu_architecture        = "X86_64"
  }

  container_definitions = jsonencode([
    {
      name      = "parabank"
      image     = var.parabank_image
      essential = true
      cpu       = 512
      memory    = 1024

      portMappings = [
        {
          containerPort = 8080
          protocol      = "tcp"
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.ecs.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "parabank"
        }
      }
    },
    {
      name      = "tests"
      image     = local.runner_image
      essential = true
      cpu       = 1536
      memory    = 3072

      dependsOn = [
        {
          containerName = "parabank"
          condition     = "START"
        }
      ]

      environment = [
        {
          name  = "LOCAL_BASE_URL"
          value = "http://localhost:8080/parabank"
        },
        {
          name  = "LOCAL_STARTUP_TIMEOUT_SECONDS"
          value = "180"
        },
        {
          name  = "PW_TIMEOUT_MS"
          value = "10000"
        },
        {
          name  = "PW_NAVIGATION_TIMEOUT_MS"
          value = "15000"
        },
        {
          name  = "REQUEST_TIMEOUT_SECONDS"
          value = "30"
        },
        {
          name  = "BLOCK_NONESSENTIAL_RESOURCES"
          value = "true"
        },
        {
          name  = "UI_SCENARIO_DELAY_SECONDS"
          value = "0"
        },
        {
          name  = "ALLURE_RESULTS_S3_BUCKET"
          value = aws_s3_bucket.allure.bucket
        }
      ]

      linuxParameters = {
        initProcessEnabled = true
      }

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.ecs.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "tests"
        }
      }
    }
  ])
}
