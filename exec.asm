.data
    var 0x01
    var2 0x01
	var3 0b10
.text
<main:0x0000>
    movri ebx, var3
	push ebx
	subri ebx, var2
	movri ecx, 0xA
	jp L2
.L1
	addri eax, var
.L2
	subri ecx, 0x1
	jg L1

	pop ebx
    halt

<func:0xAA>
	call 0xFF
	ret

<func2:0xFF>
	ret
