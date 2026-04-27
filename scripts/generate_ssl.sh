#!/bin/bash

# SSL Certificate Generation Script for Unified Commerce ERP
# Version: 1.0.0
# Description: Generate SSL certificates for production deployment

set -e

# Configuration
DOMAIN="unifiedcommerce2030.com"
SSL_DIR="./ssl"
CERT_DIR="$SSL_DIR/certs"
KEY_DIR="$SSL_DIR/private"
DAYS=365

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Functions
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Create directories
create_directories() {
    log "Creating SSL directories..."

    mkdir -p "$CERT_DIR" "$KEY_DIR"

    # Set proper permissions
    chmod 700 "$SSL_DIR"
    chmod 755 "$CERT_DIR"
    chmod 700 "$KEY_DIR"

    success "Directories created."
}

# Generate private key
generate_private_key() {
    log "Generating private key..."

    openssl genrsa -out "$KEY_DIR/$DOMAIN.key" 2048

    # Set proper permissions
    chmod 600 "$KEY_DIR/$DOMAIN.key"

    success "Private key generated."
}

# Generate certificate signing request
generate_csr() {
    log "Generating certificate signing request..."

    cat > "$SSL_DIR/$DOMAIN.cnf" << EOF
[req]
distinguished_name = req_distinguished_name
req_extensions = v3_req
prompt = no

[req_distinguished_name]
C = SA
ST = Riyadh
L = Riyadh
O = Unified Commerce 2030
OU = IT Department
CN = $DOMAIN

[v3_req]
keyUsage = keyEncipherment, dataEncipherment
extendedKeyUsage = serverAuth
subjectAltName = @alt_names

[alt_names]
DNS.1 = $DOMAIN
DNS.2 = www.$DOMAIN
DNS.3 = api.$DOMAIN
DNS.4 = app.$DOMAIN
EOF

    openssl req -new -key "$KEY_DIR/$DOMAIN.key" -out "$SSL_DIR/$DOMAIN.csr" -config "$SSL_DIR/$DOMAIN.cnf"

    success "CSR generated."
}

# Generate self-signed certificate
generate_self_signed_cert() {
    log "Generating self-signed certificate..."

    openssl x509 -req -days $DAYS -in "$SSL_DIR/$DOMAIN.csr" \
        -signkey "$KEY_DIR/$DOMAIN.key" -out "$CERT_DIR/$DOMAIN.crt" \
        -extensions v3_req -extfile "$SSL_DIR/$DOMAIN.cnf"

    success "Self-signed certificate generated."
}

# Generate DH parameters
generate_dh_params() {
    log "Generating DH parameters..."

    openssl dhparam -out "$SSL_DIR/dhparam.pem" 2048

    success "DH parameters generated."
}

# Verify certificate
verify_certificate() {
    log "Verifying certificate..."

    openssl x509 -in "$CERT_DIR/$DOMAIN.crt" -text -noout | head -20

    success "Certificate verified."
}

# Create certificate chain
create_chain() {
    log "Creating certificate chain..."

    cat "$CERT_DIR/$DOMAIN.crt" > "$CERT_DIR/$DOMAIN.chain.crt"

    success "Certificate chain created."
}

# Generate Let's Encrypt certificate (if certbot is available)
generate_letsencrypt_cert() {
    if command -v certbot &> /dev/null; then
        log "Generating Let's Encrypt certificate..."

        certbot certonly --standalone -d $DOMAIN -d www.$DOMAIN -d api.$DOMAIN -d app.$DOMAIN --agree-tos --email admin@$DOMAIN --non-interactive

        # Copy certificates to our directory
        cp "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" "$CERT_DIR/$DOMAIN.crt"
        cp "/etc/letsencrypt/live/$DOMAIN/privkey.pem" "$KEY_DIR/$DOMAIN.key"

        success "Let's Encrypt certificate generated."
    else
        warning "Certbot not found. Skipping Let's Encrypt certificate generation."
    fi
}

# Main function
main() {
    log "Starting SSL certificate generation for $DOMAIN"

    create_directories

    case "$1" in
        "self-signed")
            generate_private_key
            generate_csr
            generate_self_signed_cert
            generate_dh_params
            create_chain
            verify_certificate
            success "Self-signed SSL certificates generated successfully!"
            ;;
        "letsencrypt")
            generate_letsencrypt_cert
            generate_dh_params
            success "Let's Encrypt SSL certificates generated successfully!"
            ;;
        "verify")
            verify_certificate
            ;;
        *)
            echo "Usage: $0 {self-signed|letsencrypt|verify}"
            echo "  self-signed: Generate self-signed certificates"
            echo "  letsencrypt: Generate Let's Encrypt certificates (requires certbot)"
            echo "  verify: Verify existing certificates"
            exit 1
            ;;
    esac

    # Display certificate information
    echo
    echo "Certificate Information:"
    echo "Certificate: $CERT_DIR/$DOMAIN.crt"
    echo "Private Key: $KEY_DIR/$DOMAIN.key"
    echo "DH Params: $SSL_DIR/dhparam.pem"
    echo
    echo "Update your nginx configuration to use these certificates."
}

# Run main function with all arguments
main "$@"