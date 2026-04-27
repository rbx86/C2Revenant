# C2 Framework — Adversary Emulation Project

## Architecture

```
c2/
├── server/              # Python + Flask C2 server
│   ├── app.py           # Entry point
│   ├── config.py        # Configuration
│   ├── db/
│   │   ├── __init__.py
│   │   └── models.py    # SQLite schema + queries
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── beacon.py    # Beacon check-in & task polling
│   │   └── operator.py  # Operator CLI API
│   └── core/
│       ├── __init__.py
│       └── operator.py  # Interactive operator shell
├── beacon-rs/           # Rust beacon (implant)
│   ├── Cargo.toml
│   └── src/
│       ├── main.rs
│       ├── config.rs
│       ├── beacon.rs    # Check-in loop
│       └── executor.rs  # Command execution
└── shared/
    └── protocol.md      # JSON protocol spec
```

## Quick Start

### Server
```bash
cd server
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python app.py
```

### Beacon (on target VM)
```bash
cd beacon-rs
cargo build --release
./target/release/beacon
```

### Operator Shell
In a second terminal while server is running:
```bash
cd server
source venv/bin/activate
python -m core.operator
```
