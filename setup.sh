#!/bin/bash

# Ana dizin oluştur
mkdir -p sqlproxy-integration
cd sqlproxy-integration

# Projeleri klonla
git clone https://github.com/Teeksss/SQLProxy.git
git clone https://github.com/Teeksss/MCP-SERVER.git

# Gerekli dizinleri oluştur
mkdir -p shared
mkdir -p configs
mkdir -p logs