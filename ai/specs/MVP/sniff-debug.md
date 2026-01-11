was able to start a debug docker container
install strace
find the pid of the docker container running our app
run: strace -p 38902 -e read,write -s 1024

write(2, "INFO:src.controller_service:Switching to port 1 using Protocol.MATRIX\n", 70) = 70
write(7, "MT00SW0100NT", 12)            = 12

You are now successfully "sniffing" the serial traffic! Based on those logs, here is exactly what is happening:
1. Decoding the Logs
write(2, "INFO:...", 70): File descriptor 2 is stderr. This is your Python logger printing the "Switching to port..." message.
write(7, "MT00SW0100NT", 12) = 12: File descriptor 7 is your Serial Port. Your app successfully sent the command MT00SW0100NT (12 bytes) to the KVM.
2. Why you aren't "seeing" anything else
Since you only see write calls and no read calls immediately following them, it indicates one of three things:
The Device is not Responding: The KVM received the command but did not send an acknowledgment. This is common if the Baud Rate is wrong or the physical 3.5mm wiring (TX/RX/GND) is swapped.
Your App isn't Reading: Your Python code might be "fire and forget"—it sends the command but never calls ser.read() or ser.readline().
The Command is Invalid: If the KVM doesn't recognize MT00SW0100NT, many serial devices simply remain silent rather than sending an error.
3. How to verify the response
To see if the KVM is actually sending data back that your app is ignoring, adjust your strace to specifically look for read attempts on that same file descriptor (7):
bash
# Filter specifically for the serial port (FD 7)
strace -p [PID] -e trace=read,write -P /dev/ttyUSB0
Use code with caution.

If you see read(7, ...) and it returns -1 EAGAIN (Resource temporarily unavailable), the app is checking for data but the KVM is silent.
If you see read(7, "", 1024) = 0, the connection might have been closed.
4. Recommended Next Steps
Check Baud Rate: Most KVMs use 9600 or 115200. Double-check the manual. If you change this in your Python code, you must restart the container.
Verify the Protocol: Many "Matrix" or KVM protocols require a Line Feed (\n) or Carriage Return (\r) at the end. Your log shows MT00SW0100NT without a terminator. Try changing your Python call to:
python
ser.write(b"MT00SW0100NT\r\n")
Use code with caution.

Physical Test: If you still get no response, the 3.5mm jack on these cables is often wired differently. You may need to verify if your KVM expects Tip-RX/Ring-TX or vice versa.