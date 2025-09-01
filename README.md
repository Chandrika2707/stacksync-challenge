# Safe Python Script Execution Service

A secure, containerized API service that safely executes arbitrary Python scripts using nsjail for security isolation.

## Try It Now!

**Live Service**: https://safe-python-executor-dxrbv2b2dq-uc.a.run.app/health

### Quick Test Commands

**Health Check:**
```bash
curl https://safe-python-executor-dxrbv2b2dq-uc.a.run.app/health
```

**Basic Execution:**
```bash
curl -X POST https://safe-python-executor-dxrbv2b2dq-uc.a.run.app/execute -H "Content-Type: application/json" -d '{"script": "def main():\n    return {\"message\": \"Hello from Cloud Run!\"}"}'
```

**NumPy Example:**
```bash
curl -X POST https://safe-python-executor-dxrbv2b2dq-uc.a.run.app/execute -H "Content-Type: application/json" -d '{"script": "import numpy as np\ndef main():\n    return {\"random_number\": float(np.random.randn(1)[0])}"}'
```

---

## Features

- **Secure Execution**: Uses nsjail for process isolation and security
- **Input Validation**: Validates Python scripts before execution
- **Resource Limits**: Enforces memory, CPU, and execution time limits
- **Safe Libraries**: Access to basic libraries (os, pandas, numpy)
- **Docker Ready**: Simple deployment with Docker
- **Health Monitoring**: Built-in health check endpoint
- **Cloud Run Compatible**: Ready for Google Cloud Run deployment

## Architecture

The service uses a multi-layered security approach:

1. **nsjail Sandboxing**: Process isolation with strict resource limits
2. **Input Validation**: AST parsing to ensure valid Python syntax
3. **Resource Limits**: Memory (1GB), CPU (300s), execution time (30s)
4. **Non-root Execution**: Runs as unprivileged user
5. **Fallback Security**: Python-based security layer when nsjail is limited

## Requirements

- Docker
- Python 3.11+
- nsjail 3.4+ (built from source)

## Quick Start

### Current Deployment Status
- **Service URL**: https://safe-python-executor-dxrbv2b2dq-uc.a.run.app
- **Project ID**: `python-executor-20250901`
- **Region**: `us-central1`
- **Status**: **Live and Healthy**

### Local Development

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd <repo-name>
   ```

2. **Build the Docker image**
   ```bash
   docker build -t safe-python-executor .
   ```

3. **Run the service**
   ```bash
   docker run -p 8080:8080 safe-python-executor
   ```

4. **Test the service**
   ```bash
   curl http://localhost:8080/health
   ```

### Production Deployment

1. **Set environment variables**
   ```bash
   export PROJECT_ID="python-executor-20250901"
   export REGION="us-central1"
   ```

2. **Deploy using the script**
   ```bash
   ./deploy.sh
   ```

3. **Or deploy manually**
   ```bash
   # Build and push to container registry
   docker build -t gcr.io/${PROJECT_ID}/safe-python-executor .
   docker push gcr.io/${PROJECT_ID}/safe-python-executor
   
   # Deploy to Google Cloud Run
   gcloud run deploy safe-python-executor \
     --image gcr.io/${PROJECT_ID}/safe-python-executor \
     --platform managed \
     --region ${REGION} \
     --allow-unauthenticated \
     --port 8080
   ```

## API Usage

### Execute Python Script

**Endpoint**: `POST /execute`

**Request Body**:
```json
{
  "script": "def main():\n    return {'message': 'Hello, World!', 'data': [1, 2, 3]}"
}
```

**Response**:
```json
{
  "result": {
    "message": "Hello, World!",
    "data": [1, 2, 3]
  },
  "stdout": ""
}
```

### Health Check

**Endpoint**: `GET /health`

**Response**:
```json
{
  "status": "healthy",
  "service": "Safe Python Execution Service (Enhanced with nsjail)",
  "security": "nsjail + input validation (nsjail: available)",
  "features": [
    "resource limits",
    "dangerous import blocking",
    "sandboxed execution",
    "nsjail sandboxing"
  ]
}
```

## Security Features

### Input Validation
- Python syntax validation using AST parsing
- Required `main()` function check
- Dangerous import/function blocking:
  - `subprocess`, `eval`, `exec`, `__import__`
  - File system operations: `os.listdir`, `open`, `glob`
  - System commands and network access

### Execution Security
- nsjail sandboxing with namespace isolation
- Resource limits and timeouts
- Non-root execution
- Restricted environment variables
- Seccomp filtering (when available)

### Resource Limits
- Memory: 1GB per execution
- CPU: 300 seconds maximum
- Execution time: 30 seconds timeout
- File operations: Restricted to temporary directories

## Example Scripts

### Basic Hello World
```python
def main():
    return {"message": "Hello, World!"}
```

### Data Processing with NumPy
```python
import numpy as np

def main():
    data = np.random.randn(100)
    return {
        "mean": float(np.mean(data)),
        "std": float(np.std(data)),
        "min": float(np.min(data)),
        "max": float(np.max(data))
    }
```

### Data Analysis with Pandas
```python
import pandas as pd
import numpy as np

def main():
    # Create sample data
    df = pd.DataFrame({
        'x': np.random.randn(50),
        'y': np.random.randn(50)
    })
    
    # Calculate statistics
    stats = {
        'count': len(df),
        'correlation': float(df['x'].corr(df['y'])),
        'x_mean': float(df['x'].mean()),
        'y_mean': float(df['y'].mean())
    }
    
    return stats
```

## Testing

### Health Check
```bash
curl https://safe-python-executor-dxrbv2b2dq-uc.a.run.app/health
```

### Execute Script
```bash
curl -X POST https://safe-python-executor-dxrbv2b2dq-uc.a.run.app/execute -H "Content-Type: application/json" -d '{"script": "def main():\n    return {\"message\": \"Test successful\"}"}'
```

### Test with NumPy
```bash
curl -X POST https://safe-python-executor-dxrbv2b2dq-uc.a.run.app/execute -H "Content-Type: application/json" -d '{"script": "import numpy as np\ndef main():\n    data = np.random.randn(10)\n    return {\"mean\": float(np.mean(data)), \"data\": data.tolist()}"}'
```

### Test with Pandas
```bash
curl -X POST https://safe-python-executor-dxrbv2b2dq-uc.a.run.app/execute -H "Content-Type: application/json" -d '{"script": "import pandas as pd\nimport numpy as np\ndef main():\n    df = pd.DataFrame({\"x\": np.random.randn(5), \"y\": np.random.randn(5)})\n    return {\"correlation\": float(df[\"x\"].corr(df[\"y\"])), \"shape\": list(df.shape)}"}'
```

## Docker

### Build Image
```bash
docker build -t safe-python-executor .
```

### Run Container
```bash
docker run -p 8080:8080 safe-python-executor
```

### Image Details
- **Base**: Python 3.11-slim
- **Size**: ~856MB
- **Port**: 8080
- **User**: Non-root (appuser:1000)

## Configuration

### nsjail Configuration
The service includes a pre-configured `nsjail.cfg` with:
- Resource limits
- Namespace isolation
- Cloud Run compatibility settings
- Security policies

### Environment Variables
- `ENVIRONMENT`: Set to "production" in Cloud Run
- `PORT`: Service port (default: 8080)

## Notes

- **nsjail Limitations**: Some nsjail features may be limited in Cloud Run due to platform restrictions
- **Fallback Security**: When nsjail is limited, the service falls back to robust Python-based security
- **Resource Limits**: Adjust limits in `nsjail.cfg` and Cloud Run configuration as needed

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [nsjail](https://nsjail.dev/) - Process isolation and security
- [Google Cloud Run](https://cloud.google.com/run) - Serverless platform
- [Flask](https://flask.palletsprojects.com/) - Web framework 
