output "instance_id" {

  description = "CloudPulse EC2 instance ID."

  value = aws_instance.cloudpulse.id
}


output "public_ip" {

  description = "Public IPv4 address of the CloudPulse EC2 instance."

  value = aws_instance.cloudpulse.public_ip
}


output "public_dns" {

  description = "Public DNS name of the CloudPulse EC2 instance."

  value = aws_instance.cloudpulse.public_dns
}


output "cloudpulse_url" {

  description = "CloudPulse public application URL."

  value = "http://${aws_instance.cloudpulse.public_ip}:${var.app_port}"
}


output "ssh_command" {

  description = "SSH command for connecting to the EC2 instance."

  value = "ssh -i ~/.ssh/cloudpulse-ec2 ec2-user@${aws_instance.cloudpulse.public_ip}"
}