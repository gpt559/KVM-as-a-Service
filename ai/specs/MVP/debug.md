Check the Baud Rate
While 9600 is the standard for older TESmart models, newer 4K@60Hz/4K@120Hz models (like your X24) sometimes operate at a higher speed.

Try: 115200 baud.

Also Try: 38400 baud.

Protocol Verification (Hex Codes)
The codes you listed (0xAA 0xBB...) are for the 4-Port Enterprise models. Your HDC202-X24 is a 2-Port Dual Monitor model. These two product lines sometimes use different chipsets.

If the standard codes fail (after you verify the TX/RX wiring), try this alternative protocol used by their dual-monitor consumer line:

Alternative Protocol A (Keypad Emulation):

Header: 0x55 instead of 0xAA

CMD: 0x55 0x01 0x01 0x00 (PC1)

Alternative Protocol B (Routing Command): Sometimes the 2-port KVMs treat the "Dual Monitor" as two separate switches internally.

Try: 0xAA 0xBB 0x03 0x01 0x11 0xEE (Switch Output A to Input 1)