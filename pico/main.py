import time
import utime
import machine
from rotary_irq_rp2 import RotaryIRQ

btn_click_thresh = 300
btn_doubleclick_thresh = 150

r = RotaryIRQ(pin_num_clk=21, 
              pin_num_dt=20, 
              reverse=False, 
              range_mode=RotaryIRQ.RANGE_UNBOUNDED)

btn = machine.Pin(19, machine.Pin.IN, machine.Pin.PULL_UP)
led = machine.Pin(25, machine.Pin.OUT)

def printEnc(string, delta):
    if delta >= 0:
        status = "up"
    else:
        status = "down"
    for _ in range(abs(delta)):
        led.on()
        print(string, status)

val_old = r.value()
btn_state = "up"
btn_time = utime.ticks_ms()
while True:
    val_new = r.value()
    btn_new = btn.value()

    if val_old != val_new:
        delta = val_old - val_new
        val_old = val_new

        if btn_new == 0:
            if btn_state == "down_double":
                text = "enc1_doubleclick_scroll"
                btn_state = "down_double_scroll"
            elif btn_state == "down_double_scroll":
                text = "enc1_doubleclick_scroll"
            else:
                text = "enc1_hold_scroll"
                btn_state = "down_scroll"
            printEnc(text, delta)
        else:
            printEnc("enc1_scroll", delta)
    
    if btn_new == 0:
        if btn_state == "up":
            btn_state = "down_pre"
            btn_time = utime.ticks_ms()
        elif btn_state == "down_pre":
            if utime.ticks_ms() - btn_time > btn_click_thresh:
                led.on()
                print("sw_btn_hold")
                btn_state = "down_hold"
                btn_time = utime.ticks_ms()
        elif btn_state == "btn_click":
            if utime.ticks_ms() - btn_time <= btn_doubleclick_thresh:
                btn_state = "down_double"
                btn_time = utime.ticks_ms()
    elif btn_new == 1:
        if btn_state == "down_pre":
            if utime.ticks_ms() - btn_time <= btn_click_thresh:
                #print("sw_btn_click")
                btn_state = "btn_click"
                btn_time = utime.ticks_ms()
            else:
                btn_state = "up"
                led.on()
                print("sw_btn_up")
        elif btn_state == "btn_click":
            if utime.ticks_ms() - btn_time > btn_doubleclick_thresh:
                led.on()
                print("sw_btn_click")
                btn_state = "up"
        elif btn_state == "down_hold":
            btn_state = "up"
            led.on()
            print("sw_btn_up")
        elif btn_state == "down_double":
            btn_state = "up"
            led.on()
            print("sw_btn_doubleclick")
        else:
            btn_state = "up"

    time.sleep_ms(25)
    led.off()


