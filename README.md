# RS2 INL UAV Demo
**Risk-Surface Reduction Substrate (RS2) — Drone Identity Revocation**
Liverion Corp. | Idaho National Laboratory UAV Center

---

## What This Demonstrates

RS2 assigns a governed identity to each drone on startup. When the ground station issues a revocation command, an RS2 Revocation Event is created and recorded. The drone continues to fly — but its identity is cryptographically dead. It cannot authenticate. It cannot report as a trusted platform.

**"Fly — but not lie."**

This is the thesis: an autonomous vehicle's identity can be revoked at runtime, mid-operation, without disrupting physical operation. The same primitive applies to satellites, autonomous ground vehicles, and any unmanned system operating under a governance envelope.

---

## Requirements

- Python 3.8 or later (standard on Raspberry Pi OS Bullseye and later)
- No external Python packages — standard library only
- Laptop and Pis on the same WiFi network for the full hardware demo

---

## Option A — Local Simulation (no hardware, run on laptop)

Proves the RS2 logic without any Raspberry Pi or network.

```bash
cd 04-INL-UAV-Demo
python3 demo_local.py
```

**What you will see:**
1. Three drone Identity Objects registered and printed as JSON
2. A Revocation Event issued against `drone-002`, printed as JSON
3. A complete RS2 audit log written to `logs/demo_local_audit.json`

This is the fastest way to verify the RS2 implementation runs correctly before the hardware test.

---

## Option B — Hardware Demo (Raspberry Pi + laptop ground station)

### Step 1 — Build the Pi deployment package (run once, on your laptop)

```bash
cd 04-INL-UAV-Demo
bash package_for_pi.sh
```

This creates `rs2-inl-uav-demo.zip` — a self-contained package with all RS2 modules included.

### Step 2 — Deploy to each Raspberry Pi

For each Pi (repeat for each drone):

```bash
# From your laptop
scp rs2-inl-uav-demo.zip pi@<pi-ip-address>:~/

# SSH into the Pi
ssh pi@<pi-ip-address>

# On the Pi
unzip rs2-inl-uav-demo.zip
cd rs2-inl-uav-demo
```

### Step 3 — Configure the drone identity on each Pi

Edit `drone_config.json` before starting the agent:

```json
{
  "drone_id": "drone-001",
  "governing_authority": "urn:liverion:authority:inl-uav-center",
  "jurisdiction": "US-ID"
}
```

Use `drone-001`, `drone-002`, `drone-003` etc. on each Pi respectively.

```bash
nano drone_config.json
```

### Step 4 — Run setup on each Pi

```bash
bash setup.sh
```

### Step 5 — Start the drone agent on each Pi

```bash
python3 drone_agent.py
```

Expected output:
```
[RS2 Drone Agent] drone-001 online
  Identity registered | Authority: urn:liverion:authority:inl-uav-center
  Listening on port 9200
  Log: logs/drone-001_audit.json
```

The agent is now listening for ground station commands on port 9200.

### Step 6 — Start the ground station on the operator's laptop

```bash
cd 04-INL-UAV-Demo
python3 ground_station.py 192.168.1.101 192.168.1.102 192.168.1.103
```

Replace the IP addresses with the actual Pi IP addresses on your WiFi network.

Expected output:
```
============================================================
RS2 Ground Station — INL UAV Demo
Liverion Corp. | Risk-Surface Reduction Substrate (RS2)
============================================================

Polling 3 drone(s)...

  drone-001  (192.168.1.101)  ACTIVE
  drone-002  (192.168.1.102)  ACTIVE
  drone-003  (192.168.1.103)  ACTIVE

  Drone Status
  -------------------------------------------------------
  drone-001             192.168.1.101      ACTIVE
  drone-002             192.168.1.102      ACTIVE
  drone-003             192.168.1.103      ACTIVE

ground>
```

---

## Test Protocol

### Test sequence (run at the ground station terminal)

**T+0:00 — Confirm all drones active**
```
ground> status
```
All three drones should show `ACTIVE`. Verify drones are airborne.

**T+0:30 — Issue revocation against drone-002**
```
ground> revoke drone-002
```

**Expected result:**
- Ground station prints the RS2 Revocation Event as JSON
- Status table updates: `drone-002` shows `*** REVOKED ***`
- `drone-002` continues to fly (no physical command is sent)
- The revocation event is written to the audit log on both the Pi and the ground station

**T+1:00 — Confirm revocation is persistent**
```
ground> status
```
`drone-002` should still show `REVOKED`. `drone-001` and `drone-003` should remain `ACTIVE`.

**T+1:30 — Print complete audit log**
```
ground> log
```
The log shows the full event sequence: three identity registrations, one revocation event, all with timestamps.

**T+2:00 — Test complete**

The audit log file is written to `logs/ground_station_audit.json` on the laptop and `logs/drone-002_audit.json` on the Pi.

---

## Pass Criteria

| Check | Expected |
|-------|----------|
| All three drones register on startup | Identity Objects in log |
| Drones report ACTIVE before revocation | STATUS command confirms |
| Revocation Event JSON printed on command | RS2 RevocationEvent with `targets: ["drone-002"]` |
| drone-002 reports REVOKED after command | STATUS confirms |
| drone-002 continues to fly | Physical operation unaffected |
| drone-001 and drone-003 remain ACTIVE | STATUS confirms |
| Audit log contains all events in sequence | `log` command or JSON file |

---

## File Reference

| File | Purpose |
|------|---------|
| `demo_local.py` | Single-machine simulation — no hardware required |
| `drone_agent.py` | Runs on each Raspberry Pi; registers identity, handles revocation commands |
| `ground_station.py` | Runs on operator's laptop; polls drones, issues revocations |
| `audit_log.py` | Append-only JSON event log (shared by both agent and ground station) |
| `setup.sh` | One-time Pi setup script |
| `package_for_pi.sh` | Builds `rs2-inl-uav-demo.zip` for Pi deployment |
| `drone_config.json` | Per-Pi drone identity configuration (created by setup.sh) |
| `logs/` | Audit log output directory |

---

## About RS2

RS2 (Risk-Surface Reduction Substrate) is a 10-primitive semantic identity substrate developed by Liverion Corp. This demo exercises two of those primitives:

- **Identity Object** — governs the existence and referential continuity of each drone under the INL authority
- **Revocation Event** — declaratively terminates an identity's validity with a timestamped, scoped, authority-issued record

The audit log produced here is the precursor to Liverion's cryptographic proof layer — currently in development — that makes every Revocation Event permanently non-repudiable and compliant with regulated audit requirements.

**37 U.S. Patents Pending — Perkins Coie**

Contact: Chris Blanchard, Ph.D. | chris@liverion.io | +1-208-392-8726
