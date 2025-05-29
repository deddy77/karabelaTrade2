# Docker Maintenance Guide

## Regular Maintenance Tasks

### 1. Check System Resources
```bash
# Check Docker disk usage
./cleanup_docker.sh space

# Monitor container resources
./manage_bot.sh monitor
```

### 2. Cleanup Unused Resources
```bash
# Safe cleanup (removes only unused resources)
./cleanup_docker.sh safe

# Full cleanup (WARNING: removes everything!)
./cleanup_docker.sh full
```

### 3. Update Container
```bash
# Pull latest changes
git pull

# Rebuild container
./manage_bot.sh rebuild
```

## Common Issues and Solutions

### 1. Disk Space Issues
If Docker is using too much disk space:
1. Run disk usage check: `./cleanup_docker.sh space`
2. Perform safe cleanup: `./cleanup_docker.sh safe`
3. Remove unused images: `docker image prune`
4. Remove unused volumes: `docker volume prune`

### 2. Container Performance
If container performance degrades:
1. Monitor resources: `./manage_bot.sh monitor`
2. Check logs: `./manage_bot.sh logs`
3. Restart container: `./manage_bot.sh restart`
4. Rebuild if necessary: `./manage_bot.sh rebuild`

### 3. Network Issues
- Check Docker network: `docker network ls`
- Inspect network: `docker network inspect kbt2_network`
- Recreate network: 
  ```bash
  docker-compose down
  docker network prune
  docker-compose up -d
  ```

## Best Practices

### 1. Regular Monitoring
- Check logs daily
- Monitor resource usage
- Review performance metrics
- Track disk space usage

### 2. Maintenance Schedule
Weekly:
- Run safe cleanup
- Check logs for issues
- Monitor resource usage

Monthly:
- Update container
- Full system check
- Backup important data

### 3. Backup Procedures
1. Backup configuration:
   ```bash
   cp config.py config.backup.py
   ```

2. Backup data:
   ```bash
   tar -czf data_backup.tar.gz data/
   ```

3. Backup logs:
   ```bash
   tar -czf logs_backup.tar.gz logs/
   ```

### 4. Version Control
- Always use tagged versions
- Test updates in staging
- Keep backup of working config
- Document changes

## Troubleshooting

### 1. Container Won't Start
```bash
# Check logs
./manage_bot.sh logs

# Check container status
docker ps -a

# Try rebuilding
./manage_bot.sh rebuild
```

### 2. Resource Exhaustion
```bash
# Check resource usage
docker stats

# Memory issues
docker update --memory 4g kbt2_bot

# CPU issues
docker update --cpus 2 kbt2_bot
```

### 3. Network Connectivity
```bash
# Test network
docker network inspect kbt2_network

# Check connectivity
docker exec kbt2_bot ping -c 4 8.8.8.8
```

## Health Checks

### 1. System Health
```bash
# Check container health
docker inspect --format='{{.State.Health.Status}}' kbt2_bot

# View health check logs
docker inspect --format='{{json .State.Health}}' kbt2_bot
```

### 2. Log Analysis
```bash
# Check error logs
grep ERROR logs/karabela.log

# Check warning logs
grep WARNING logs/karabela.log
```

### 3. Performance Metrics
```bash
# Container stats
docker stats kbt2_bot

# Resource usage over time
./manage_bot.sh monitor
```

## Security Maintenance

### 1. Regular Updates
```bash
# Update base image
docker pull python:3.8-slim

# Rebuild with updates
./manage_bot.sh rebuild
```

### 2. Security Checks
- Review Docker security best practices
- Check container privileges
- Monitor network access
- Review volume permissions

### 3. Access Control
- Use non-root user
- Limit container capabilities
- Control volume mounts
- Monitor access logs

## Emergency Procedures

### 1. Quick Stop
```bash
# Stop container
./manage_bot.sh stop

# Force stop if necessary
docker kill kbt2_bot
```

### 2. Data Recovery
```bash
# Mount volume for recovery
docker run --rm -v kbt2_data:/data -v $(pwd):/backup alpine \
    tar -czf /backup/data_recovery.tar.gz /data
```

### 3. System Reset
```bash
# Full cleanup
./cleanup_docker.sh full

# Rebuild from scratch
./docker_deploy.sh
