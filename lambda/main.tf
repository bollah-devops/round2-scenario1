# Step 1 — IAM role that Lambda will assume when it runs
resource "aws_iam_role" "lambda_role" {
  name = "auto-shutdown-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}

# Step 2 — Policy giving Lambda permission to describe and stop EC2 instances
resource "aws_iam_role_policy" "lambda_ec2_policy" {
  name = "lambda-ec2-stop-policy"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ec2:DescribeInstances",
          "ec2:StopInstances"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "*"
      }
    ]
  })
}

# Step 3 — Zip the Python file so AWS can upload it
data "archive_file" "lambda_zip" {
  type        = "zip"
  source_file = "${path.module}/auto_shutdown.py"
  output_path = "${path.module}/auto_shutdown.zip"
}

# Step 4 — The Lambda function itself
resource "aws_lambda_function" "auto_shutdown" {
  filename         = data.archive_file.lambda_zip.output_path
  function_name    = "ec2-auto-shutdown"
  role             = aws_iam_role.lambda_role.arn
  handler          = "auto_shutdown.lambda_handler"
  runtime          = "python3.11"
  timeout          = 60
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256

  environment {
    variables = {
      REGION = "us-east-1"
    }
  }
}

# Step 5 — EventBridge rule to trigger Lambda every night at midnight UTC
resource "aws_cloudwatch_event_rule" "nightly_shutdown" {
  name                = "nightly-ec2-shutdown"
  description         = "Triggers EC2 auto shutdown every night at midnight UTC"
  schedule_expression = "cron(0 0 * * ? *)"
}

# Step 6 — Connect the EventBridge rule to the Lambda function
resource "aws_cloudwatch_event_target" "shutdown_target" {
  rule      = aws_cloudwatch_event_rule.nightly_shutdown.name
  target_id = "AutoShutdownTarget"
  arn       = aws_lambda_function.auto_shutdown.arn
}

# Step 7 — Allow EventBridge to invoke the Lambda function
resource "aws_lambda_permission" "allow_eventbridge" {
  statement_id  = "AllowEventBridgeInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.auto_shutdown.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.nightly_shutdown.arn
}
