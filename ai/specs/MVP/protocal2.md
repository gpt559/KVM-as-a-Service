The "Matrix" ASCII Protocol
This is the most common alternative for TESmart devices that support independent monitor switching (Matrix Mode). Instead of raw Hex bytes, it uses readable text strings.

Serial Settings:

Baud Rate: Try 115200 first (newer Matrix/Dock models often use this), then 9600.

Data/Stop: 8 Bits, 1 Stop Bit, No Parity.

Command Format: MT00SW[Input][Output]NT

Input: 01 (PC1), 02 (PC2)

Output: 00 (All Monitors), 01 (Monitor A), 02 (Monitor B)

Command List: | Action | ASCII Command String | | :--- | :--- | | Switch Monitor A to PC 1 | MT00SW0101NT | | Switch Monitor A to PC 2 | MT00SW0201NT | | Switch Monitor B to PC 1 | MT00SW0102NT | | Switch Monitor B to PC 2 | MT00SW0202NT | | Switch ALL to PC 1 | MT00SW0100NT | | Mute Buzzer | MT00BZM00NT | | Unmute Buzzer | MT00BZM01NT |

2. The "Dual-Monitor" Hex Protocol (Variant)
Some TESmart "Docking" KVMs (HDC series) use the standard 0xAA header but use different opcodes for the audio and independent display functions.

Hex Codes: | Action | Hex Sequence | | :--- | :--- | | Mute Buzzer | 0xAA 0xBB 0x03 0x02 0x00 0xEE | | Unmute Buzzer | 0xAA 0xBB 0x03 0x02 0x01 0xEE | | Switch Output A to PC1 | 0xAA 0xBB 0x03 0x10 0x01 0xEE (Try opcode 0x10 for Output A) | | Switch Output B to PC1 | 0xAA 0xBB 0x03 0x11 0x01 0xEE (Try opcode 0x11 for Output B) |

(Note: The 0x02 opcode for the buzzer is consistent across almost all TESmart hex protocols. If this specific command does not make the unit beep/silent, your issue is 100% wiring or baud rate, not the protocol.)