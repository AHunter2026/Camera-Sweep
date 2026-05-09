from machine import Pin, PWM
from config import SERVO_PIN, MIN_DUTY, MAX_DUTY

servo = PWM(Pin(SERVO_PIN))
servo.freq(50)

def set_angle(angle: int):
    """Convert angle (0-180) to PWM duty and move servo"""
    duty = int(MIN_DUTY + (MAX_DUTY - MIN_DUTY) * angle / 180)
    servo.duty_u16(duty)