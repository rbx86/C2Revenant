# C2 Communication Protocol

All messages are JSON over HTTP. The beacon always initiates contact.

---

## 1. Beacon Check-in (Registration + Heartbeat)

**POST** `/api/beacon/checkin`

The beacon sends this on startup and every N seconds (with jitter).

### Request Body
```json
{
  "uuid": "550e8400-e29b-41d4-a716-446655440000",
  "hostname": "DESKTOP-ABC123",
  "username": "john",
  "os": "Linux 6.8.0",
  "arch": "x86_64",
  "pid": 1337,
  "sleep": 60,
  "jitter": 10
}
```

### Response Body (server → beacon)
```json
{
  "status": "ok",
  "registered": true
}
```

---

## 2. Task Poll (beacon asks for work)

**GET** `/api/beacon/<uuid>/tasks`

The beacon calls this after every check-in to see if there are pending tasks.

### Response — no tasks
```json
{
  "tasks": []
}
```

### Response — with tasks
```json
{
  "tasks": [
    {
      "task_id": "a1b2c3d4",
      "type": "shell",
      "payload": {
        "cmd": "whoami"
      }
    }
  ]
}
```

---

## 3. Task Result Submission

**POST** `/api/beacon/<uuid>/result`

The beacon sends this after executing a task.

### Request Body
```json
{
  "task_id": "a1b2c3d4",
  "type": "shell",
  "exit_code": 0,
  "stdout": "john\n",
  "stderr": "",
  "exec_time_ms": 42
}
```

### Response
```json
{
  "status": "ok"
}
```

---

## Task Types

| Type    | Payload fields | Description               |
|---------|---------------|---------------------------|
| `shell` | `cmd: string` | Run a shell command via sh |

---

## Error Response (any endpoint)
```json
{
  "status": "error",
  "message": "human readable reason"
}
```

---

## Sleep & Jitter

Actual sleep time is calculated as:
```
sleep_actual = sleep + random(-jitter, +jitter)
sleep_actual = max(1, sleep_actual)
```
