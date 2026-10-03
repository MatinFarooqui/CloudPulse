variable "aws_account_id" {

  description = "AWS account ID used to protect Terraform from targeting the wrong account."

  type = string
}


variable "aws_region" {

  description = "AWS region for the CloudPulse deployment."

  type = string

  default = "ap-south-1"
}


variable "instance_type" {

  description = "EC2 instance type."

  type = string

  default = "t3.micro"
}


variable "ssh_cidr" {

  description = "Public IPv4 CIDR allowed to connect over SSH."

  type = string
}


variable "public_key_path" {

  description = "Path to the CloudPulse EC2 public SSH key."

  type = string

  default = "~/.ssh/cloudpulse-ec2.pub"
}


variable "key_name" {

  description = "AWS EC2 key pair name."

  type = string

  default = "cloudpulse-ec2"
}


variable "app_port" {

  description = "Public CloudPulse application port."

  type = number

  default = 8000
}


variable "github_repo" {

  description = "Public GitHub repository containing CloudPulse."

  type = string

  default = "https://github.com/MatinFarooqui/CloudPulse.git"
}


variable "db_name" {

  description = "PostgreSQL database name."

  type = string

  default = "cloudpulse"
}


variable "db_user" {

  description = "PostgreSQL username."

  type = string

  default = "cloudpulse"
}


variable "db_password" {

  description = "PostgreSQL password used by the CloudPulse deployment."

  type = string

  sensitive = true
}