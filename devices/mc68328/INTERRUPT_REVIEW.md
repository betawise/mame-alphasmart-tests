# DragonBall interrupt review

References supplied locally:

- Motorola MC68EZ328 User's Manual, sections 6.6.3 (IMR), 6.6.4 (ISR),
  and 6.6.5 (IPR). The EZ328 is the AS3000's actual processor.
- Motorola MC68328 User's Manual, sections 6.5.3, 6.5.5 and 6.5.6.
  Both variants use the modified base-class methods.

The manuals specify that a masked request remains visible in IPR, but does
not appear in ISR or request a CPU interrupt. An unmasked pending request
appears in both registers. ISR means interrupt **status**, not an independent
CPU "in service" latch. CPU interrupt masking is separate from this peripheral
controller's IMR.

The original USB wake fix removed an ISR test that prevented reasserting a
pending source after an IMR mask/unmask cycle. Review found that this fix
alone did not correct two existing problems: masked bits remained in ISR,
and masking one source could incorrectly lower a CPU level still requested
by another source. The updated methods now update the affected ISR bits from
IPR and IMR, then drive the CPU level from all pending unmasked sources at
that level. Mask writes update all changed levels.

`test_mc68328_interrupts.py` compiles the actual production
methods with a minimal CPU-line fixture. It checks masked requests, ISR/IPR
visibility, repeated mask/unmask without a new edge, source removal, two
sources sharing a level, and simultaneous mask changes at different levels.
This does not claim a complete audit of the SoC: external edge detection,
write-one-to-clear handling, and configurable interrupt priority remain
outside this change's validation.
