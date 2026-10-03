terraform {
  required_version = ">= 1.6.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "6.66.0"
    }
  }
}

provider "aws" {
  region = var.aws_region

  allowed_account_ids = [
    var.aws_account_id
  ]

  default_tags {
    tags = {
      Project     = "CloudPulse"
      Environment = "Demo"
      ManagedBy   = "Terraform"
    }
  }
}


# ---------------------------------------------------------
# Existing default VPC
# ---------------------------------------------------------

data "aws_vpc" "default" {
  default = true
}


# ---------------------------------------------------------
# Public subnet from the default VPC
# ---------------------------------------------------------

data "aws_subnets" "default" {

  filter {
    name = "vpc-id"

    values = [
      data.aws_vpc.default.id
    ]
  }
}


# ---------------------------------------------------------
# Latest Amazon Linux 2023 x86_64 AMI
# ---------------------------------------------------------

data "aws_ssm_parameter" "al2023_ami" {

  name = "/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64"
}


# ---------------------------------------------------------
# EC2 SSH key pair
# ---------------------------------------------------------

resource "aws_key_pair" "cloudpulse" {

  key_name = var.key_name

  public_key = file(
    pathexpand(var.public_key_path)
  )

  tags = {
    Name = "CloudPulse EC2 Key"
  }
}


# ---------------------------------------------------------
# Security Group
# ---------------------------------------------------------

resource "aws_security_group" "cloudpulse" {

  name = "cloudpulse-sg"

  description = "Security group for CloudPulse EC2"

  vpc_id = data.aws_vpc.default.id


  # SSH only from the user's current public IP
  ingress {

    description = "SSH from deployment workstation"

    from_port = 22
    to_port   = 22

    protocol = "tcp"

    cidr_blocks = [
      var.ssh_cidr
    ]
  }


  # CloudPulse dashboard
  ingress {

    description = "CloudPulse application"

    from_port = var.app_port
    to_port   = var.app_port

    protocol = "tcp"

    cidr_blocks = [
      "0.0.0.0/0"
    ]
  }


  # Allow outbound traffic
  egress {

    description = "Allow outbound IPv4 traffic"

    from_port = 0
    to_port   = 0

    protocol = "-1"

    cidr_blocks = [
      "0.0.0.0/0"
    ]
  }


  tags = {
    Name = "CloudPulse Security Group"
  }
}


# ---------------------------------------------------------
# CloudPulse EC2 instance
# ---------------------------------------------------------

resource "aws_instance" "cloudpulse" {

  ami = data.aws_ssm_parameter.al2023_ami.value

  instance_type = var.instance_type

  subnet_id = sort(
    data.aws_subnets.default.ids
  )[0]

  associate_public_ip_address = true

  key_name = aws_key_pair.cloudpulse.key_name

  vpc_security_group_ids = [
    aws_security_group.cloudpulse.id
  ]


  # Avoid unexpected T3 Unlimited CPU-credit charges
  credit_specification {

    cpu_credits = "standard"
  }


  # Bootstrap the server
  user_data = templatefile(
    "${path.module}/user-data.sh",

    {
      github_repo = var.github_repo

      db_name = var.db_name

      db_user = var.db_user

      db_password = var.db_password
    }
  )


  # Small encrypted root disk
  root_block_device {

    volume_size = 10

    volume_type = "gp3"

    encrypted = true

    delete_on_termination = true
  }


  # Require IMDSv2
  metadata_options {

    http_endpoint = "enabled"

    http_tokens = "required"
  }


  tags = {
    Name = "CloudPulse-Server"
  }


  # The AMI is selected from the AWS public SSM parameter.
  # Ignore later AMI updates so terraform apply does not
  # unexpectedly replace the running demo server.
  lifecycle {

    ignore_changes = [
      ami
    ]
  }
}