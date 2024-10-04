provider "google" {
  project = var.gcp_project
  region  = var.gcp_region
}

variable "gcp_project" {}

variable "host_count" {
}

variable "gcp_region" {
  default = "europe-west3"
}

variable "gcp_zone" {
  default = "a"
}

variable "host_type" {
  default = "n2-standard-16"
}

output "zone" {
  value = local.zone
}

output "host_ip_internal" {
  value = google_compute_instance.komet-host.*.network_interface.0.network_ip
}

output "host_name" {
  value = formatlist("%s.%s.%s", google_compute_instance.komet-host.*.name, local.zone, var.gcp_project)
}

output "host_id" {
  value = google_compute_instance.komet-host.*.name
}

output "project" {
  value = var.gcp_project
}

# the zone variable must be within the region
# hence this weird setup
locals {
  zone = "${var.gcp_region}-${var.gcp_zone}"
}

# we use a version of Ubuntu 22.04 LTS
# this data item gives us the latest available image
data "google_compute_image" "ubuntu2204image" {
  family  = "ubuntu-2204-lts"
  project = "ubuntu-os-cloud"
}

# we want our instances to be able to talk to each other directly
# hence we add them all to a dedicated network
resource "google_compute_network" "komet-network" {
  name                    = "komet-network"
  description             = "This network connects Celestial hosts."
  auto_create_subnetworks = true
}

resource "google_compute_firewall" "komet-net-firewall-internal" {
  name        = "komet-net-firewall-internal"
  description = "This firewall allows internal communication in the network."
  direction   = "INGRESS"
  network     = google_compute_network.komet-network.id
  source_tags = ["komet-host"]

  allow {
    protocol = "all"
  }
}

# we also need to enable ingress to our machines
resource "google_compute_firewall" "komet-net-firewall-external" {
  name          = "komet-net-firewall-external"
  description   = "This firewall allows external connections to our instance for ssh."
  network       = google_compute_network.komet-network.id
  direction     = "INGRESS"
  source_ranges = ["0.0.0.0/0"]

  allow {
    protocol = "tcp"
    ports    = ["22"]
  }
}

# reserve a static external IP address
# makes rebooting the host easier
resource "google_compute_address" "komet-host-ip" {
  name  = "komet-host-ip-${count.index}"
  count = var.host_count
}

# we need to create an image for our hosts
# this needs a custom license to use nested virtualization
resource "google_compute_image" "komet-host-image" {
  name         = "komet-host-image"
  source_image = data.google_compute_image.ubuntu2204image.self_link
  licenses     = ["https://www.googleapis.com/compute/v1/projects/ubuntu-os-cloud/global/licenses/ubuntu-2204-lts", "https://www.googleapis.com/compute/v1/projects/vm-options/global/licenses/enable-vmx"]
}

# the host instance runs Ubuntu 22.04
resource "google_compute_instance" "komet-host" {
  name                      = "komet-host-${count.index}"
  machine_type              = var.host_type
  zone                      = local.zone
  count                     = var.host_count
  allow_stopping_for_update = true

  boot_disk {
    initialize_params {
      size  = 128 # 64GB for swap, 64GB for files
      image = google_compute_image.komet-host-image.self_link
      type  = "pd-ssd"
    }
  }

  # adapter for internal network
  network_interface {
    network = google_compute_network.komet-network.id
    # use the static IP address
    access_config {
      nat_ip = google_compute_address.komet-host-ip[count.index].address
    }
  }

  service_account {
    scopes = ["cloud-platform"]
  }

  tags = ["komet-host"]
}
