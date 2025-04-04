import serial
import time
from handGesture import HandDetector

def main():
    detector = HandDetector()
    try:
        with serial.Serial('/dev/ttyUSB0', 9600, timeout=1) as ser:
            ser.flush()
            print("System initialization complete. Starting detection...")
            
            while True:
                try:
                    num_fingers, hand_x = detector.get_fingers()
                    print(f"Fingers: {num_fingers}, X: {hand_x if hand_x else 'No hand'}")
                    
                    cmd_angle = 90
                    motor_cmd = 0
                    
                    # Activation logic
                    if num_fingers >= 2 and hand_x is not None:
                        cmd_angle = int(110 - (hand_x * 40))
                        cmd_angle = max(60, min(110, cmd_angle))
                        motor_cmd = 1
                    
                    # Send command
                    command = f"{cmd_angle},{motor_cmd}\n"
                    ser.write(command.encode())
                    time.sleep(0.08)
                    
                except KeyboardInterrupt:
                    print("\nUser requested shutdown...")
                    break
                except Exception as e:
                    print(f"Runtime error: {str(e)}")
                    time.sleep(0.5)
                    
    except serial.SerialException as e:
        print(f"Serial connection failed: {str(e)}")
    finally:
        detector.close()
        print("Resources cleaned up successfully")

if __name__ == "__main__":
    main()
