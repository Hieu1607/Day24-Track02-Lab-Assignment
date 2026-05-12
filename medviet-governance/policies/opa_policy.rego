package medviet.data_access

import future.keywords.if
import future.keywords.in

# Default: deny all
default allow := false
default deny := false

# Admin được phép tất cả
allow if {
    input.user.role == "admin"
    not deny
}

# ML Engineer được đọc training data và model artifacts
allow if {
    input.user.role == "ml_engineer"
    input.resource in {"training_data", "model_artifacts", "aggregated_metrics"}
    input.action in {"read", "write"}
    not deny
}

deny if {
    input.user.role == "ml_engineer"
    input.resource == "production_data"
    input.action == "delete"
}

allow if {
    input.user.role == "data_analyst"
    input.resource == "aggregated_metrics"
    input.action == "read"
    not deny
}

allow if {
    input.user.role == "data_analyst"
    input.resource == "reports"
    input.action == "write"
    not deny
}

allow if {
    input.user.role == "intern"
    input.resource == "sandbox_data"
    input.action in {"read", "write"}
    not deny
}

# Rule: không ai được export restricted data ra ngoài VN servers
deny if {
    input.data_classification == "restricted"
    input.destination_country != "VN"
}
