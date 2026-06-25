output "app_server_ip" {
  value = module.ec2.app_public_ip
  description = "Public IP of the app server"
}

output "app_instance_id" {
value = module.ec2.app_instance_id
}

