#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Performance Benchmark Script for ERP Application
================================================

This script measures the performance of the ERP application, specifically:
- Startup memory footprint (Idle state)
- Memory consumption after Lazy Loading (Inventory tab)
- Performance comparison report

Requirements:
    pip install psutil

Usage:
    python benchmark_app.py
"""

import subprocess
import psutil
import time
import sys
import os
from pathlib import Path
from typing import Optional, Dict, List
from datetime import datetime


class PerformanceMonitor:
    """Monitor application performance metrics"""
    
    def __init__(self, app_path: str = "main.py"):
        self.app_path = app_path
        self.process: Optional[subprocess.Popen] = None
        self.process_info: Optional[psutil.Process] = None
        self.metrics: Dict[str, float] = {}
        self.startup_time: Optional[float] = None
        self.idle_memory_mb: Optional[float] = None
        self.loaded_memory_mb: Optional[float] = None
        
    def find_python_executable(self) -> str:
        """Find the Python executable"""
        return sys.executable
    
    def start_application(self) -> bool:
        """Start the application and monitor startup"""
        print("=" * 70)
        print("🚀 Starting ERP Application Performance Benchmark")
        print("=" * 70)
        print()
        
        # Check if main.py exists
        if not os.path.exists(self.app_path):
            print(f"❌ Error: {self.app_path} not found!")
            print(f"   Current directory: {os.getcwd()}")
            return False
        
        print(f"📁 Application path: {os.path.abspath(self.app_path)}")
        print(f"🐍 Python executable: {self.find_python_executable()}")
        print()
        
        # Start the application
        print("⏳ Launching application...")
        start_time = time.time()
        
        try:
            # Start the process
            self.process = subprocess.Popen(
                [self.find_python_executable(), self.app_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=os.getcwd()
            )
            
            # Get process info using psutil
            self.process_info = psutil.Process(self.process.pid)
            
            # Wait a bit for the app to initialize
            print("⏳ Waiting for application to initialize (5 seconds)...")
            time.sleep(5)
            
            # Measure startup time
            self.startup_time = time.time() - start_time
            
            print(f"✅ Application started successfully!")
            print(f"   Process ID: {self.process.pid}")
            print(f"   Startup time: {self.startup_time:.2f} seconds")
            print()
            
            return True
            
        except Exception as e:
            print(f"❌ Error starting application: {e}")
            return False
    
    def measure_idle_memory(self) -> bool:
        """Measure memory consumption in idle state (after startup)"""
        print("=" * 70)
        print("📊 Phase 1: Measuring Idle Memory (Startup State)")
        print("=" * 70)
        print()
        
        if not self.process_info:
            print("❌ Error: Application process not found!")
            return False
        
        try:
            # Wait a bit more to ensure app is fully idle
            print("⏳ Waiting for application to stabilize (3 seconds)...")
            time.sleep(3)
            
            # Measure memory multiple times and take average
            memory_samples: List[float] = []
            print("📈 Collecting memory samples (5 samples over 5 seconds)...")
            
            for i in range(5):
                try:
                    memory_info = self.process_info.memory_info()
                    memory_mb = memory_info.rss / (1024 * 1024)  # Convert to MB
                    memory_samples.append(memory_mb)
                    print(f"   Sample {i+1}/5: {memory_mb:.2f} MB")
                    time.sleep(1)
                except psutil.NoSuchProcess:
                    print("❌ Error: Application process terminated!")
                    return False
                except Exception as e:
                    print(f"⚠️  Warning: Error collecting sample: {e}")
            
            # Calculate average
            self.idle_memory_mb = sum(memory_samples) / len(memory_samples)
            
            print()
            print(f"✅ Idle Memory Measurement Complete")
            print(f"   Average Memory: {self.idle_memory_mb:.2f} MB")
            print(f"   Min: {min(memory_samples):.2f} MB")
            print(f"   Max: {max(memory_samples):.2f} MB")
            print()
            
            return True
            
        except Exception as e:
            print(f"❌ Error measuring idle memory: {e}")
            return False
    
    def wait_for_lazy_loading(self) -> bool:
        """Wait for user to trigger Lazy Loading (Inventory tab)"""
        print("=" * 70)
        print("📊 Phase 2: Measuring Memory After Lazy Loading")
        print("=" * 70)
        print()
        
        if not self.process_info:
            print("❌ Error: Application process not found!")
            return False
        
        print("⚠️  MANUAL ACTION REQUIRED:")
        print("   Please click on the '📦 المخزون' (Inventory) tab in the application window.")
        print("   This will trigger Lazy Loading of the Inventory page.")
        print()
        
        # Countdown
        for i in range(5, 0, -1):
            print(f"   Starting measurement in {i} seconds...", end='\r')
            time.sleep(1)
        
        print("   " + " " * 50)  # Clear line
        print()
        print("📈 Monitoring memory consumption after Lazy Loading...")
        print("   (Collecting samples for 10 seconds...)")
        print()
        
        # Measure memory after Lazy Loading
        memory_samples: List[float] = []
        peak_memory = 0.0
        
        try:
            for i in range(10):
                try:
                    memory_info = self.process_info.memory_info()
                    memory_mb = memory_info.rss / (1024 * 1024)  # Convert to MB
                    memory_samples.append(memory_mb)
                    
                    if memory_mb > peak_memory:
                        peak_memory = memory_mb
                    
                    # Show progress
                    progress = "█" * (i + 1) + "░" * (10 - i - 1)
                    print(f"   [{progress}] {memory_mb:.2f} MB (Peak: {peak_memory:.2f} MB)", end='\r')
                    time.sleep(1)
                    
                except psutil.NoSuchProcess:
                    print()
                    print("❌ Error: Application process terminated!")
                    return False
                except Exception as e:
                    print()
                    print(f"⚠️  Warning: Error collecting sample: {e}")
            
            print()  # New line after progress
            
            # Calculate average
            avg_memory = sum(memory_samples) / len(memory_samples)
            self.loaded_memory_mb = peak_memory  # Use peak as loaded memory
            
            print()
            print(f"✅ Lazy Loading Memory Measurement Complete")
            print(f"   Peak Memory: {self.loaded_memory_mb:.2f} MB")
            print(f"   Average Memory: {avg_memory:.2f} MB")
            print(f"   Min: {min(memory_samples):.2f} MB")
            print(f"   Max: {max(memory_samples):.2f} MB")
            print()
            
            return True
            
        except Exception as e:
            print()
            print(f"❌ Error measuring loaded memory: {e}")
            return False
    
    def generate_report(self):
        """Generate performance comparison report"""
        print("=" * 70)
        print("📋 PERFORMANCE BENCHMARK REPORT")
        print("=" * 70)
        print()
        print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Startup Metrics
        print("🚀 STARTUP METRICS")
        print("-" * 70)
        if self.startup_time:
            print(f"   Startup Time:     {self.startup_time:.2f} seconds")
        else:
            print(f"   Startup Time:     N/A")
        print()
        
        # Memory Metrics
        print("💾 MEMORY CONSUMPTION")
        print("-" * 70)
        if self.idle_memory_mb:
            print(f"   Idle Memory:      {self.idle_memory_mb:.2f} MB")
        else:
            print(f"   Idle Memory:      N/A")
        
        if self.loaded_memory_mb:
            print(f"   Loaded Memory:    {self.loaded_memory_mb:.2f} MB")
        else:
            print(f"   Loaded Memory:    N/A")
        
        if self.idle_memory_mb and self.loaded_memory_mb:
            memory_increase = self.loaded_memory_mb - self.idle_memory_mb
            memory_increase_percent = (memory_increase / self.idle_memory_mb) * 100
            print(f"   Memory Increase:  {memory_increase:.2f} MB ({memory_increase_percent:+.1f}%)")
        print()
        
        # Performance Analysis
        print("📊 PERFORMANCE ANALYSIS")
        print("-" * 70)
        
        if self.idle_memory_mb and self.loaded_memory_mb:
            # Evaluate idle memory
            if self.idle_memory_mb < 100:
                idle_status = "✅ EXCELLENT"
            elif self.idle_memory_mb < 200:
                idle_status = "✅ GOOD"
            elif self.idle_memory_mb < 300:
                idle_status = "⚠️  ACCEPTABLE"
            else:
                idle_status = "❌ HIGH"
            
            print(f"   Idle Memory Status:    {idle_status}")
            
            # Evaluate Lazy Loading
            if self.loaded_memory_mb > self.idle_memory_mb:
                lazy_loading_status = "✅ WORKING"
                print(f"   Lazy Loading Status:   {lazy_loading_status}")
                print(f"   → Memory increased only after user action (Lazy Loading confirmed)")
            else:
                lazy_loading_status = "⚠️  CHECK"
                print(f"   Lazy Loading Status:   {lazy_loading_status}")
                print(f"   → Memory did not increase significantly (may need investigation)")
            
            # Memory efficiency
            if memory_increase < 50:
                efficiency_status = "✅ EFFICIENT"
            elif memory_increase < 100:
                efficiency_status = "✅ ACCEPTABLE"
            else:
                efficiency_status = "⚠️  HIGH INCREASE"
            
            print(f"   Memory Efficiency:      {efficiency_status}")
            print(f"   → Loaded memory increase: {memory_increase:.2f} MB")
        
        print()
        print("=" * 70)
        print("✅ Benchmark Complete!")
        print("=" * 70)
        print()
    
    def cleanup(self):
        """Clean up resources"""
        if self.process:
            try:
                print("🧹 Cleaning up...")
                print("   Terminating application process...")
                self.process.terminate()
                
                # Wait for graceful shutdown
                try:
                    self.process.wait(timeout=5)
                    print("   ✅ Application terminated gracefully")
                except subprocess.TimeoutExpired:
                    print("   ⚠️  Force killing application...")
                    self.process.kill()
                    self.process.wait()
                    print("   ✅ Application force killed")
                
            except Exception as e:
                print(f"   ⚠️  Error during cleanup: {e}")


def main():
    """Main benchmark execution"""
    print()
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 15 + "ERP Application Performance Benchmark" + " " * 15 + "║")
    print("╚" + "═" * 68 + "╝")
    print()
    
    # Check if psutil is installed
    try:
        import psutil
    except ImportError:
        print("❌ Error: psutil library not found!")
        print()
        print("Please install it using:")
        print("   pip install psutil")
        print()
        sys.exit(1)
    
    # Create monitor
    monitor = PerformanceMonitor(app_path="main.py")
    
    try:
        # Phase 1: Start application and measure idle memory
        if not monitor.start_application():
            print("❌ Failed to start application. Exiting...")
            sys.exit(1)
        
        if not monitor.measure_idle_memory():
            print("❌ Failed to measure idle memory. Exiting...")
            monitor.cleanup()
            sys.exit(1)
        
        # Phase 2: Wait for Lazy Loading and measure loaded memory
        if not monitor.wait_for_lazy_loading():
            print("❌ Failed to measure loaded memory. Exiting...")
            monitor.cleanup()
            sys.exit(1)
        
        # Generate report
        monitor.generate_report()
        
    except KeyboardInterrupt:
        print()
        print()
        print("⚠️  Benchmark interrupted by user")
        monitor.cleanup()
        sys.exit(0)
    except Exception as e:
        print()
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        monitor.cleanup()
        sys.exit(1)
    finally:
        # Cleanup
        monitor.cleanup()
        print()
        print("👋 Goodbye!")


if __name__ == "__main__":
    main()




