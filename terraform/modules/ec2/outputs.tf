output "app_instance_id" { value = aws_instance.app_server.id }
output "app_public_ip" { value = aws_instance.app_server.public_ip }