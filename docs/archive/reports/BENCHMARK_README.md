# Performance Benchmark Script

## 📋 Overview

`benchmark_app.py` is a standalone performance testing script that measures the ERP application's memory consumption and verifies Lazy Loading implementation.

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install psutil
```

### 2. Run Benchmark

```bash
python scripts/benchmark_app.py
```

## 📊 What It Measures

### Phase 1: Idle Memory (Startup State)
- Measures RAM consumption immediately after application launch
- Collects 5 samples over 5 seconds
- **Goal**: Low memory footprint (< 200 MB ideal)

### Phase 2: Loaded Memory (After Lazy Loading)
- Waits for you to click the "📦 المخزون" (Inventory) tab
- Monitors memory for 10 seconds after tab click
- **Goal**: Memory should increase only after user action (Lazy Loading confirmed)

## 📈 Report Output

The script generates a comprehensive report showing:

```
🚀 STARTUP METRICS
   Startup Time:     X.XX seconds

💾 MEMORY CONSUMPTION
   Idle Memory:      XXX.XX MB
   Loaded Memory:    XXX.XX MB
   Memory Increase:  XX.XX MB (+XX.X%)

📊 PERFORMANCE ANALYSIS
   Idle Memory Status:    ✅ EXCELLENT / ✅ GOOD / ⚠️ ACCEPTABLE / ❌ HIGH
   Lazy Loading Status:   ✅ WORKING (Memory increased only after user action)
   Memory Efficiency:      ✅ EFFICIENT / ✅ ACCEPTABLE / ⚠️ HIGH INCREASE
```

## ✅ Success Criteria

1. **Idle Memory**: Should be < 200 MB (Excellent) or < 300 MB (Acceptable)
2. **Lazy Loading**: Memory should increase only after clicking Inventory tab
3. **Memory Efficiency**: Increase should be < 100 MB after loading Inventory

## ⚠️ Manual Steps

During Phase 2, the script will prompt you:
```
⚠️  MANUAL ACTION REQUIRED:
   Please click on the '📦 المخزون' (Inventory) tab in the application window.
```

**You have 5 seconds** to click the tab before measurement begins.

## 🧹 Cleanup

The script automatically terminates the application process after completion. If interrupted (Ctrl+C), it will also clean up properly.

## 📝 Notes

- The script uses `psutil` to monitor the application process
- Memory measurements are in MB (RSS - Resident Set Size)
- The script waits for the application to stabilize before measurements
- Multiple samples are taken to ensure accuracy

