Thanks a lot for your detailed message and for double-checking this before trying more things – that’s very much appreciated.
To clarify the interface on our side:
The 3.5 mm service port uses UART with TTL levels, not true RS-232.
The logic level is 3.3 V TTL (about 0 V for “0” and 3.3 V for “1”).
The electrical pinout of the 3.5 mm UART port is:
Pin 3 – TX
Pin 2 – RX
Pin 1 – GND
The UART uses standard (non-inverted) TTL levels and supports bidirectional communication via TX and RX.

 

Regarding the cables you mentioned:
You should use a 3.3 V TTL USB-to-serial cable (like the first link you shared).
Please do not use a true RS-232 cable (like the second link). RS-232 interfaces typically use ±12 V levels, and as you were told, this can indeed damage a port that is designed for 3.3 V TTL.