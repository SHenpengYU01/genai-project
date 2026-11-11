## Appendix A: Per-task formal specifications

| ID | Task | Difficulty | Source | POU | LTL specifications |
| --- | --- | --- | --- | --- | --- |
| public_easy_001 | Automated filling line control | easy | Public | `FillingLine` | **P1**: `G(!(Pump_Motor && Filling_Valve) && !(Filling_Valve && Capping_Machine) && !(Capping_Machine && Packing_Machine) && !(Packing_Machine && Completion_Light))`<br>**P2**: `G(bottleSensor -> X(Pump_Motor))`<br>**P3**: `G((Pump_Motor && cleaningConfirmButton) -> X(Filling_Valve))`<br>**P4**: `G((Packing_Machine && packingConfirmButton) -> X(Completion_Light))`<br>**P5**: `G((Completion_Light && finishedButton) -> X(!Completion_Light))` |
| public_easy_002 | Double-word edge detection | easy | Public | `EdgeDetect` | **P1**: `G(hasChanged -> (risingBits <> 0 || fallingBits <> 0))`<br>**P2**: `G((risingBits <> 0) <-> hasRisingEdges)`<br>**P3**: `G((fallingBits <> 0) <-> hasFallingEdges)`<br>**P4**: `G((risingBits AND fallingBits) = 0)` |
| public_easy_003 | Alarm handling with hysteresis | easy | Public | `AlarmHyst` | **P1**: `G((!error && Value > hiLevel) -> hiAlarm)`<br>**P2**: `G((!error && Value < hiLevel - hystWindow) -> !hiAlarm)`<br>**P3**: `G((!error && Value < loLevel) -> loAlarm)`<br>**P4**: `G((!error && Value > loLevel + hystWindow) -> !loAlarm)`<br>**P5**: `G((loLevel >= hiLevel) -> error)` |
| public_easy_004 | Jam pump debouncing and run maintenance | easy | Public | `JamPump` | **P1**: `G(!PASTE_E_STOP_NC -> !VFD_RUN)`<br>**P2**: `G(!VISCOSITY_OK -> X(!VFD_RUN))`<br>**P3**: `G(PUMP_RUNTIME_ACC <= X(PUMP_RUNTIME_ACC))` |
| public_easy_005 | Weld-gap alarm and start inhibition | easy | Public | `WeldGap` | **P1**: `G(!Weld_E_Stop_NC -> !Operator_Alert)`<br>**P2**: `G(Weld_Soft_Start_Active -> !Operator_Alert)`<br>**P3**: `G(Operator_Alert -> Gap_Exceeded)`<br>**P4**: `G(F(!Weld_Soft_Start_Active))` |
| public_easy_006 | Aeration blower delayed start | easy | Public | `AerationBlower` | **P1**: `G(!AERATION_E_STOP_NC -> !BLOWER_RUN)`<br>**P2**: `G(BLOWER_RUN -> DO_LOW)`<br>**P3**: `G(AERATION_BLOWER_CYCLE_COUNT <= X(AERATION_BLOWER_CYCLE_COUNT))` |
| self_easy_001 | Two-phase traffic light | easy | Self-built | `TrafficLight` | **P1**: `G(!(NS_Green && EW_Green))`<br>**P2**: `G(NS_Green || EW_Green)` |
| self_easy_002 | Tank level control with high-high alarm | easy | Self-built | `TankLevel` | **P1**: `G(level > highHighLevel -> highHighAlarm)`<br>**P2**: `G(level < lowLevel -> pumpOn)` |
| self_easy_003 | Automatic door control | easy | Self-built | `AutoDoor` | **P1**: `G(!(openCmd && closeCmd))`<br>**P2**: `G(presence -> openCmd)` |
| public_medium_001 | Multi-pump rotating water supply | medium | Public | `MultiPump` | **P1**: `G(stop -> !pumpGroup[1].RunComd)`<br>**P2**: `G((!mode && !stop && start && pumpGroup[1].selection) -> pumpGroup[1].RunComd)`<br>**P3**: `G((!mode && !stop && start && !pumpGroup[1].selection) -> !pumpGroup[1].RunComd)` |
| public_medium_002 | Moving average computation | medium | Public | `MovingAverage` | **P1**: `G((windowSize < 1 || windowSize > 100) -> error)`<br>**P2**: `G(!error -> status = 0)` |
| public_medium_003 | Temperature control logic | medium | Public | `TempControl` | **P1**: `G((TemperatureSensorInput < 0 || TemperatureSensorInput > 100) -> !HeaterOutput)`<br>**P2**: `G((TemperatureSensorInput < SetTemperature && !OverheatProtection) -> HeaterOutput)`<br>**P3**: `G(OverheatProtection -> !HeaterOutput)` |
| public_medium_004 | Analog batch conversion | medium | Public | `AnalogBatch` | **P1**: `G((channels[0].enable && (channels[0].measuringMode < 0 || channels[0].measuringMode > 2)) -> channels[0].retVal = 16#8001)`<br>**P2**: `G((channels[0].enable && channels[0].hiLIM <= channels[0].loLIM) -> channels[0].retVal = 16#8002)` |
| public_medium_005 | Automated production line control | medium | Public | `ProductionLine` | **P1**: `G(!(MotorForward && MotorReverse))`<br>**P2**: `G((!Mode && ForwardButton && !ReverseButton) -> MotorForward)`<br>**P3**: `G(CompletionLight -> SensorC)` |
| public_medium_006 | Slab thickness alarm and fault history | medium | Public | `SlabThickness` | **P1**: `G(!THICKNESS_SIGNAL_VALID -> !THICKNESS_ALARM)`<br>**P2**: `G(THICKNESS_ALARM -> THICKNESS_SIGNAL_VALID)`<br>**P3**: `G(Slab_Fault_Counter <= X(Slab_Fault_Counter))` |
| public_medium_007 | Office HVAC multi-mode energy-saving control | medium | Public | `HVAC` | **P1**: `G(HVAC_MODE_SELECTOR = 3 -> !SUPPLY_FAN_RUN)`<br>**P2**: `G(TEMP_SETPOINT_ADJUST >= -4 && TEMP_SETPOINT_ADJUST <= 4)`<br>**P3**: `G((HVAC_MODE_SELECTOR = 0 && !OCCUPANCY_DETECTED && ENERGY_SAVING_MODE) -> TEMP_SETPOINT_ADJUST = 3)` |
| public_medium_008 | IPv4 address parsing | medium | Public | `IPv4Parse` | **P1**: `G(ipValue <= 16#FFFFFFFF)` |
| self_medium_001 | Conveyor height sorting | medium | Self-built | `HeightSort` | **P1**: `G(binSel >= 1 && binSel <= 3)` |
| self_medium_002 | Duty/standby pump alternation | medium | Self-built | `PumpAlternation` | **P1**: `G(stop -> (!pump1Run && !pump2Run))`<br>**P2**: `G(!(pump1Run && pump2Run))` |
| self_medium_003 | Alarm latching with acknowledge and reset | medium | Self-built | `AlarmLatch` | **P1**: `G(acknowledge -> !horn)`<br>**P2**: `G(reset -> !alarmLatched)` |
| self_medium_004 | Star-delta reduced-voltage start | medium | Self-built | `StarDelta` | **P1**: `G(!(starContactor && deltaContactor))`<br>**P2**: `G(overload -> (!mainContactor && !starContactor && !deltaContactor))` |
| public_hard_001 | Recipe management system | hard | Public | `RecipeMgmt` | **P1**: `G(!error -> status = 0)`<br>**P2**: `G(error -> (status = 16#8001 || status = 16#8002 || status = 16#8003 || status = 16#8004 || status = 16#8005))` |
| public_hard_002 | Material batching process control | hard | Public | `MaterialMix` | **P1**: `G(!estop -> (!valveARun && !valveBRun && !valveCRun && !valveDRun && !mixMotorRun))`<br>**P2**: `G((!opeMode && estop && valveAStart && !X(valveAStart)) -> (valveARun <-> !X(valveARun)))` |
| public_hard_003 | Five-station production control | hard | Public | `ProductionControl` | **P1**: `G(!(MotorForward && MotorReverse))`<br>**P2**: `G(CompletionLight -> SensorOutput)`<br>**P3**: `G(firingTemp >= 500.0 && firingTemp <= 550.0)` |
| public_hard_004 | Flexible machining control | hard | Public | `FlexProcess` | **P1**: `G(!(conveyorLeft && conveyorRight))`<br>**P2**: `G((sensor1 && station1Start) -> F(sensor5))` |
| public_hard_005 | Robotic arm control | hard | Public | `MechArm` | **P1**: `G(!EmergencyStop -> (!MoveDown && !MoveUp && !MoveLeft && !MoveRight && !ActivateGrip && !ActivateRelease))` |
| public_hard_006 | FIFO first-in-first-out queue | hard | Public | `FifoQueue` | **P1**: `G(elementCount >= 0 && elementCount <= 10)`<br>**P2**: `G((reset || elementCount = 0) -> (status = 0 || status = 16#8001))` |
| self_hard_001 | Parking lot occupancy counting | hard | Self-built | `ParkingLot` | **P1**: `G(count >= 0 && count <= capacity)`<br>**P2**: `G(count >= capacity -> !entryGate)` |
| self_hard_002 | Constant-pressure multi-pump staging | hard | Self-built | `ConstPressure` | **P1**: `G(pressure < setpoint - deadband -> (pump1Run || pump2Run || pump3Run))`<br>**P2**: `G(pressure > setpoint + deadband -> (!pump1Run && !pump2Run && !pump3Run))` |
| self_hard_003 | Three-floor elevator control | hard | Self-built | `Elevator` | **P1**: `G(!(motorUp && motorDown))`<br>**P2**: `G(doorOpen -> (!motorUp && !motorDown))` |

## Appendix B: Tasks that did not succeed

| Setting | Task | Difficulty | Termination status | Rounds | Blocker |
| --- | --- | --- | --- | --- | --- |
| Self-built+DeepSeek | public_easy_005 | easy | max_rounds | 5 | Tests failed |
| Self-built+DeepSeek | self_easy_003 | easy | no_progress | 3 | Tests failed |
| Self-built+Qwen | public_easy_004 | easy | max_rounds | 5 | Tests failed |
| Self-built+Qwen | public_easy_005 | easy | no_progress | 3 | Tests failed |
| Self-built+Qwen | self_easy_001 | easy | max_rounds | 5 | Tests failed |
| Self-built+Qwen | self_easy_003 | easy | no_progress | 3 | Tests failed |
| Codex+DeepSeek | self_easy_003 | easy | no_progress | 3 | Tests failed |
| Codex+Qwen | public_easy_004 | easy | max_rounds | 5 | Compile failed |
| Codex+Qwen | public_easy_005 | easy | no_progress | 4 | Tests failed |
| Codex+Qwen | self_easy_001 | easy | max_rounds | 5 | Tests failed |
| Codex+Qwen | self_easy_003 | easy | no_progress | 4 | Tests failed |
| Self-built+DeepSeek | public_medium_005 | medium | stalled | 4 | Tests failed |
| Self-built+Qwen | public_medium_003 | medium | no_progress | 3 | Tests failed |
| Self-built+Qwen | public_medium_004 | medium | max_rounds | 5 | Compile failed |
| Codex+DeepSeek | public_medium_003 | medium | max_rounds | 5 | Tests failed |
| Codex+DeepSeek | public_medium_005 | medium | no_progress | 3 | Tests failed |
| Codex+Qwen | public_medium_001 | medium | max_rounds | 5 | Tests failed |
| Codex+Qwen | public_medium_002 | medium | max_rounds | 5 | Tests failed |
| Codex+Qwen | public_medium_003 | medium | max_rounds | 5 | Compile failed |
| Codex+Qwen | public_medium_004 | medium | max_rounds | 5 | Tests failed |
| Codex+Qwen | public_medium_006 | medium | max_rounds | 5 | Compile failed |
| Codex+Qwen | public_medium_008 | medium | max_rounds | 5 | Compile failed |
| Codex+Qwen | self_medium_002 | medium | max_rounds | 5 | Tests failed |
| Self-built+DeepSeek | public_hard_003 | hard | no_progress | 3 | Tests failed |
| Self-built+DeepSeek | public_hard_004 | hard | no_progress | 3 | Tests failed |
| Self-built+Qwen | public_hard_003 | hard | no_progress | 3 | Tests failed |
| Self-built+Qwen | public_hard_004 | hard | no_progress | 5 | Tests failed |
| Self-built+Qwen | public_hard_006 | hard | max_rounds | 5 | Compile failed |
| Self-built+Qwen | self_hard_003 | hard | max_rounds | 5 | Tests failed |
| Codex+DeepSeek | public_hard_003 | hard | no_progress | 3 | Tests failed |
| Codex+DeepSeek | public_hard_004 | hard | no_progress | 3 | Tests failed |
| Codex+Qwen | public_hard_002 | hard | max_rounds | 5 | Tests failed |
| Codex+Qwen | public_hard_003 | hard | max_rounds | 5 | Compile failed |
| Codex+Qwen | public_hard_005 | hard | max_rounds | 5 | Tests failed |
| Codex+Qwen | public_hard_006 | hard | max_rounds | 5 | Tests failed |
| Codex+Qwen | self_hard_003 | hard | max_rounds | 5 | Tests failed |

## Appendix C: Per-task four-setting results (all tests passed?)

| Task | Difficulty | Title | Self-built+DeepSeek | Self-built+Qwen | Codex+DeepSeek | Codex+Qwen |
| --- | --- | --- | --- | --- | --- | --- |
| public_easy_001 | easy | Automated filling line control | ✓ | ✓ | ✓ | ✓ |
| public_easy_002 | easy | Double-word edge detection | ✓ | ✓ | ✓ | ✓ |
| public_easy_003 | easy | Alarm handling with hysteresis | ✓ | ✓ | ✓ | ✓ |
| public_easy_004 | easy | Jam pump debouncing and run maintenance | ✓ | ✗ | ✓ | ✗ |
| public_easy_005 | easy | Weld-gap alarm and start inhibition | ✗ | ✗ | ✓ | ✗ |
| public_easy_006 | easy | Aeration blower delayed start | ✓ | ✓ | ✓ | ✓ |
| self_easy_001 | easy | Two-phase traffic light | ✓ | ✗ | ✓ | ✗ |
| self_easy_002 | easy | Tank level control with high-high alarm | ✓ | ✓ | ✓ | ✓ |
| self_easy_003 | easy | Automatic door control | ✗ | ✗ | ✗ | ✗ |
| public_medium_001 | medium | Multi-pump rotating water supply | ✓ | ✓ | ✓ | ✗ |
| public_medium_002 | medium | Moving average computation | ✓ | ✓ | ✓ | ✗ |
| public_medium_003 | medium | Temperature control logic | ✓ | ✗ | ✗ | ✗ |
| public_medium_004 | medium | Analog batch conversion | ✓ | ✗ | ✓ | ✗ |
| public_medium_005 | medium | Automated production line control | ✗ | ✓ | ✗ | ✓ |
| public_medium_006 | medium | Slab thickness alarm and fault history | ✓ | ✓ | ✓ | ✗ |
| public_medium_007 | medium | Office HVAC multi-mode energy-saving control | ✓ | ✓ | ✓ | ✓ |
| public_medium_008 | medium | IPv4 address parsing | ✓ | ✓ | ✓ | ✗ |
| self_medium_001 | medium | Conveyor height sorting | ✓ | ✓ | ✓ | ✓ |
| self_medium_002 | medium | Duty/standby pump alternation | ✓ | ✓ | ✓ | ✗ |
| self_medium_003 | medium | Alarm latching with acknowledge and reset | ✓ | ✓ | ✓ | ✓ |
| self_medium_004 | medium | Star-delta reduced-voltage start | ✓ | ✓ | ✓ | ✓ |
| public_hard_001 | hard | Recipe management system | ✓ | ✓ | ✓ | ✓ |
| public_hard_002 | hard | Material batching process control | ✓ | ✓ | ✓ | ✗ |
| public_hard_003 | hard | Five-station production control | ✗ | ✗ | ✗ | ✗ |
| public_hard_004 | hard | Flexible machining control | ✗ | ✗ | ✗ | ✓ |
| public_hard_005 | hard | Robotic arm control | ✓ | ✓ | ✓ | ✗ |
| public_hard_006 | hard | FIFO first-in-first-out queue | ✓ | ✗ | ✓ | ✗ |
| self_hard_001 | hard | Parking lot occupancy counting | ✓ | ✓ | ✓ | ✓ |
| self_hard_002 | hard | Constant-pressure multi-pump staging | ✓ | ✓ | ✓ | ✓ |
| self_hard_003 | hard | Three-floor elevator control | ✓ | ✗ | ✓ | ✗ |
