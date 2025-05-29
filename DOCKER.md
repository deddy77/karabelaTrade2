# Docker Deployment Guide

## Prerequisites

- Docker installed and running
- Docker Compose installed
- Python 3.8 or higher

## Quick Start

### Windows
```batch
manage_bot.bat start
```

### Linux/Mac
```bash
./manage_bot.sh start
```

## Container Management

The bot comes with management scripts that provide the following commands:

- `start` - Start the bot container
- `stop` - Stop the bot container
- `restart` - Restart the bot container
- `status` - Show container status
- `logs` - Show container logs
- `stats` - Show resource usage
- `rebuild` - Rebuild and restart container
- `monitor` - Monitor container status and resources

### Examples

```bash
# Start the bot
./manage_bot.sh start

# View logs
./manage_bot.sh logs

# Monitor container
./manage_bot.sh monitor

# Rebuild container
./manage_bot.sh rebuild
```

## Configuration

### Environment Variables

Create a `.env` file with your MT5 credentials:
```env
MT5_LOGIN=your_login
MT5_PASSWORD=your_password
MT5_SERVER=your_server
```

### Volumes

The container uses these volumes:
- `/app/config.py` - Bot configuration
- `/app/data` - Data storage
- `/app/logs` - Log files

### Ports
- 8080 - Reserved for future web interface

## Manual Deployment

### Build Image
```bash
docker-compose build
```

### Start Container
```bash
docker-compose up -d
```

### Stop Container
```bash
docker-compose down
```

## Development with Docker

### Running Tests
```bash
docker-compose run --rm tradingbot python -m pytest
```

### Shell Access
```bash
docker-compose exec tradingbot /bin/bash
```

### View Logs
```bash
docker-compose logs -f
```

## Troubleshooting

1. Container won't start:
   - Check Docker status: `docker info`
   - Check logs: `manage_bot.sh logs`
   - Verify MT5 credentials in .env

2. GUI issues:
   - On Linux, ensure X11 forwarding is configured
   - Check DISPLAY environment variable

3. Performance issues:
   - Monitor resources: `manage_bot.sh monitor`
   - Check system resources with `docker stats`

## Security Notes

1. Always use a non-root user (configured in Dockerfile)
2. Keep MT5 credentials secure
3. Use read-only mounts where possible
4. Regularly update base images
5. Monitor container logs

## Resource Requirements

Recommended minimum:
- 2 CPU cores
- 4GB RAM
- 20GB disk space

## Updates and Maintenance

1. Pull latest changes:
   ```bash
   git pull
   ```

2. Rebuild container:
   ```bash
   manage_bot.sh rebuild
   ```

3. Check logs for errors:
   ```bash
   manage_bot.sh logs
   ```

## Health Checks

The container includes health checks that verify:
1. MT5 connection
2. System resources
3. Core services

View health status:
```bash
docker inspect --format='{{.State.Health.Status}}' kbt2_bot
