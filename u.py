from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_CENTER

OUTPUT = "/mnt/user-data/outputs/Unit2_Exam_Answers.pdf"
doc = SimpleDocTemplate(OUTPUT, pagesize=A4,
    leftMargin=18*mm, rightMargin=18*mm, topMargin=16*mm, bottomMargin=16*mm)
W = A4[0] - 36*mm

C_DARK  = colors.HexColor("#1a1a2e")
C_ACC   = colors.HexColor("#2563eb")
C_LIGHT = colors.HexColor("#eff6ff")
C_RULE  = colors.HexColor("#93c5fd")
C_MUTED = colors.HexColor("#64748b")
C_AMBER = colors.HexColor("#92400e")
C_ABG   = colors.HexColor("#fef3c7")
C_GRAY  = colors.HexColor("#f1f5f9")
C_HEAD  = colors.HexColor("#1e3a5f")
C_SBGC  = colors.HexColor("#dbeafe")
C_GBG   = colors.HexColor("#f0fdf4")
C_GREEN = colors.HexColor("#166534")

def S(n,**k): return ParagraphStyle(n,**k)
sT  = S("t", fontName="Helvetica-Bold",  fontSize=18, textColor=C_DARK, leading=22, spaceAfter=4,  alignment=TA_CENTER)
sSb = S("sb",fontName="Helvetica",        fontSize=10, textColor=C_MUTED,leading=13, spaceAfter=12, alignment=TA_CENTER)
sQ  = S("q", fontName="Helvetica-Bold",  fontSize=11, textColor=C_ACC,  leading=15, spaceBefore=10,spaceAfter=4)
sB  = S("b", fontName="Helvetica",        fontSize=10, textColor=C_DARK, leading=15, spaceAfter=4)
sBl = S("bl",fontName="Helvetica",        fontSize=10, textColor=C_DARK, leading=15, spaceAfter=2, leftIndent=14)
sF  = S("f", fontName="Helvetica-BoldOblique",fontSize=10,textColor=C_ACC,leading=14,spaceAfter=4,leftIndent=10)

def rule():   return HRFlowable(width="100%",thickness=0.5,color=C_RULE,spaceAfter=6)
def sp(n=6):  return Spacer(1,n)
def b(t):     return Paragraph(f"\u2022  {t}", sBl)
def p(t):     return Paragraph(t, sB)
def q(t):     return Paragraph(t, sQ)
def f(t):     return Paragraph(t, sF)

def sec(num, title):
    tbl = Table([[Paragraph(f"Q{num} \u2014 {title}",
                  S("sh",fontName="Helvetica-Bold",fontSize=12,textColor=C_HEAD,leading=16))]],
                colWidths=[W])
    tbl.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),C_SBGC),
        ("TOPPADDING",(0,0),(-1,-1),7),("BOTTOMPADDING",(0,0),(-1,-1),7),
        ("LEFTPADDING",(0,0),(-1,-1),10)]))
    return tbl

def tip(text):
    tbl = Table([[Paragraph(f"<b>Exam Tip:</b> {text}",
                  S("tb",fontName="Helvetica",fontSize=9.5,textColor=C_AMBER,leading=13))]],
                colWidths=[W])
    tbl.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),C_ABG),
        ("TOPPADDING",(0,0),(-1,-1),6),("BOTTOMPADDING",(0,0),(-1,-1),6),
        ("LEFTPADDING",(0,0),(-1,-1),10)]))
    return tbl

def ct(headers, rows, cw=None):
    if cw is None: cw=[W/len(headers)]*len(headers)
    data=[[Paragraph(f"<b>{h}</b>",S("ch",fontName="Helvetica-Bold",fontSize=9.5,
            textColor=C_HEAD,leading=12)) for h in headers]]
    for row in rows:
        data.append([Paragraph(c,S("cd",fontName="Helvetica",fontSize=9.5,
                       textColor=C_DARK,leading=13)) for c in row])
    t=Table(data,colWidths=cw)
    st=[("BACKGROUND",(0,0),(-1,0),C_LIGHT),("GRID",(0,0),(-1,-1),0.5,C_RULE),
        ("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5),
        ("LEFTPADDING",(0,0),(-1,-1),7),("VALIGN",(0,0),(-1,-1),"TOP")]
    for i in range(1,len(data)):
        st.append(("BACKGROUND",(0,i),(-1,i),colors.white if i%2==0 else C_GRAY))
    t.setStyle(TableStyle(st))
    return t

def nb(text):
    tbl=Table([[Paragraph(text,S("nb",fontName="Helvetica",fontSize=10,
                textColor=C_GREEN,leading=15))]],colWidths=[W])
    tbl.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),C_GBG),
        ("LINEBEFORE",(0,0),(0,-1),3,colors.HexColor("#86efac")),
        ("TOPPADDING",(0,0),(-1,-1),7),("BOTTOMPADDING",(0,0),(-1,-1),7),
        ("LEFTPADDING",(0,0),(-1,-1),12)]))
    return tbl

# ════════════════════════════════════════════════════════════════
story = []
story += [sp(4),Paragraph("Unit 2 — Complete Exam Answer Guide",sT),
          Paragraph("All 10 questions \u2022 Simple language \u2022 Paper-ready answers",sSb),
          rule(),sp(8)]

# ─── Q1 ─────────────────────────────────────────────────────────
story += [sec(1,"Define Actuator — Classify Pneumatic, Hydraulic, Electrical with Merits/Demerits"),sp(8)]
story += [
    q("Q1. Define an actuator. Classify actuators into pneumatic, hydraulic, and electrical types with examples, merits, and demerits."),sp(4),
    p("<b>Definition of an Actuator:</b>"),
    p("An actuator is a device that converts energy (air pressure, oil pressure, or electricity) into mechanical motion or force. It is the 'muscle' of any machine — it receives a control signal and performs physical work such as pushing, pulling, rotating, or gripping."),sp(6),
    p("<b>Classification of Actuators:</b>"),sp(4),
    p("<b>1. Pneumatic Actuators</b> — use compressed air as working medium."),
    b("Examples: Pneumatic cylinders, air motors, pneumatic grippers."),
    b("<b>Merits:</b> Fast response, clean (no oil leaks), safe in food/pharma environments, simple design, low cost."),
    b("<b>Demerits:</b> Limited force (air compresses — 'spongy' feel), noisy exhaust, needs a separate air compressor."),sp(4),
    p("<b>2. Hydraulic Actuators</b> — use pressurized oil as working medium."),
    b("Examples: Hydraulic cylinders, hydraulic motors, hydraulic presses."),
    b("<b>Merits:</b> Extremely high force output, rigid and precise positioning (oil is incompressible), smooth operation under heavy loads."),
    b("<b>Demerits:</b> Risk of oil leaks (fire hazard, environmental pollution), slow response, high maintenance, bulky infrastructure."),sp(4),
    p("<b>3. Electrical Actuators</b> — use electrical energy as working medium."),
    b("Examples: DC motors, stepper motors, servo motors, BLDC motors, solenoids."),
    b("<b>Merits:</b> Highly precise (digital feedback encoders), easy to control and program, clean and quiet, wide speed and torque range."),
    b("<b>Demerits:</b> Limited torque at low speeds (without gearbox), sensitive to moisture and dust (needs IP rating), requires power electronics."),sp(6),
]
story += [ct(["Parameter","Pneumatic","Hydraulic","Electrical"],
    [["Working medium","Compressed air","Pressurized oil","AC/DC electricity"],
     ["Force/Load","Low to medium","Extremely high","Medium to high"],
     ["Speed","Very fast","Moderate to slow","Fast to moderate"],
     ["Precision","Low (air compresses)","High (incompressible oil)","Very high (encoder feedback)"],
     ["Cleanliness","Clean, safe","Oil leaks, fire risk","Clean, quiet"],
     ["Cost","Low","High","Medium"],
     ["Best use","Pick-and-place, food lines","Cranes, excavators, presses","Robots, CNC machines"]],
    cw=[W*0.20,W*0.26,W*0.27,W*0.27]),sp(6),
    tip("This is a 10-mark Q — write definition, then explain all 3 types with examples, list 3 merits and 3 demerits each, and finish with the comparison table."),sp(12)]

# ─── Q2 ─────────────────────────────────────────────────────────
story += [sec(2,"Pneumatic Actuators — Construction, Working, Merits, Demerits, Applications"),sp(8)]
story += [
    q("Q2. Explain pneumatic actuators with a neat sketch. Discuss construction, working principle, merits, demerits, and applications."),sp(4),
    p("<b>What is a Pneumatic Actuator?</b>"),
    p("A pneumatic actuator converts the energy of compressed air into mechanical motion (linear or rotary). It is widely used in automation systems for fast, clean, and simple motion control."),sp(6),
    p("<b>Types of Pneumatic Actuators:</b>"),
    b("<b>Linear (Cylinder):</b> Converts air pressure into straight-line push/pull motion. Most common type."),
    b("<b>Rotary (Air Motor):</b> Converts air pressure into continuous rotation."),sp(6),
    p("<b>Construction of a Pneumatic Cylinder (Linear Actuator):</b>"),
    b("<b>Cylinder Barrel:</b> Smooth-bore steel tube that contains the air and guides the piston."),
    b("<b>Piston:</b> Disc inside the barrel with rubber seals that divides it into two chambers and converts air pressure into linear force."),
    b("<b>Piston Rod:</b> Hardened steel rod attached to the piston that extends out of the cylinder to do mechanical work."),
    b("<b>End Caps (Front and Rear):</b> Seal both ends of the barrel. The rear cap is sealed (blind end). The front cap has a hole for the piston rod."),
    b("<b>Air Ports:</b> Two inlet/outlet openings — one at each end — for pressurized air to enter and exhaust to exit."),
    b("<b>Seals/O-rings:</b> Rubber seals around the piston and rod prevent air leakage between chambers."),sp(6),
    p("<b>Working Principle — Double-Acting Cylinder:</b>"),
    p("A double-acting cylinder uses compressed air for both the forward stroke (extension) and the return stroke (retraction):"),
    b("<b>Extension stroke:</b> Compressed air enters the blind-end port → pushes the full piston face area → rod extends outward. Rod-end port vents to atmosphere."),
    b("<b>Retraction stroke:</b> Compressed air enters the rod-end port → pushes the annular area (piston minus rod) → rod retracts. Blind-end port vents."),
    f("Force = Pressure (P) × Area (A)     Extension force > Retraction force (full area vs annular area)"),
    p("<b>Single-Acting Cylinder:</b> Air only on one side. A spring returns the piston. Simpler but less force on return."),sp(6),
]
story += [ct(["Feature","Merits","Demerits"],
    [["Force","Adequate for light-medium tasks","Limited force — air compresses (spongy)"],
     ["Speed","Very fast response","Speed depends on airflow control"],
     ["Safety","Clean — safe for food/pharma","Exhaust noise can be significant"],
     ["Maintenance","Simple design, easy to maintain","Needs air compressor and dryer/filter"],
     ["Cost","Low component cost","High infrastructure cost (compressor)"]],
    cw=[W*0.18,W*0.41,W*0.41]),sp(6),
    p("<b>Applications:</b>"),
    b("Pick-and-place robots in assembly lines."),
    b("Food and pharmaceutical packaging lines (clean environment required)."),
    b("Conveyor sorting gates and diverters."),
    b("Clamping and material handling fixtures."),
    b("Door opening/closing systems in automated machinery."),sp(6),
    tip("Draw the cylinder cross-section showing: barrel, piston, piston rod, blind-end port, rod-end port, and seals. Label the extension and retraction strokes with arrows. A neat labeled sketch earns 4 marks by itself."),sp(12)]

# ─── Q3 ─────────────────────────────────────────────────────────
story += [sec(3,"Hydraulic Actuator — Working, Merits, Demerits, Compare with Pneumatic"),sp(8)]
story += [
    q("Q3. Describe the hydraulic actuator system. Explain working principle, merits, demerits, and compare with pneumatic actuators."),sp(4),
    p("<b>What is a Hydraulic Actuator?</b>"),
    p("A hydraulic actuator uses pressurized oil (hydraulic fluid) to generate very large mechanical forces and precise motion. It is used wherever extremely high force is needed — heavy construction, industrial presses, and earthmoving equipment."),sp(6),
    p("<b>Main Components of a Hydraulic System:</b>"),
    b("<b>Hydraulic Pump:</b> Driven by an electric motor or engine. Pressurizes the hydraulic oil and forces it through the system."),
    b("<b>Control Valve (Directional Control Valve / DCV):</b> Directs the flow of oil into either side of the cylinder to control direction of motion."),
    b("<b>Hydraulic Cylinder:</b> The actuator itself. Same construction as a pneumatic cylinder but built for much higher pressures (100–400+ bar). Contains piston, piston rod, seals, and ports."),
    b("<b>Reservoir (Oil Tank):</b> Stores the hydraulic oil. Also helps cool and filter the oil."),
    b("<b>Pressure Relief Valve:</b> Safety valve that opens if system pressure exceeds the safe limit — prevents damage."),
    b("<b>Return Lines and Filters:</b> Oil returns to the reservoir after doing work. Filters remove contaminants."),sp(6),
    p("<b>Working Principle:</b>"),
    p("Pascal's Law states that pressure applied to a confined fluid is transmitted equally in all directions. The hydraulic actuator uses this:"),
    b("The pump pressurizes the oil to high pressure (e.g. 200 bar)."),
    b("The DCV directs this high-pressure oil into one side of the cylinder."),
    b("The oil pushes on the large piston area, generating massive force."),
    b("The piston rod extends, doing mechanical work (lifting, pressing, pushing)."),
    b("To retract, the DCV reverses — oil enters the rod side, rod side oil returns to reservoir."),
    f("Force = Pressure × Piston Area   e.g. 200 bar × 50 cm² = 100,000 N = 100 kN"),sp(6),
]
story += [ct(["Feature","Hydraulic","Pneumatic"],
    [["Working fluid","Pressurized oil (100–400 bar)","Compressed air (5–10 bar)"],
     ["Force output","Extremely high — tonnes of force","Low to medium"],
     ["Precision","Very high (oil incompressible)","Low (air is compressible, spongy)"],
     ["Speed","Moderate to slow (oil is viscous)","Very fast (air is light)"],
     ["Cleanliness","Oil leaks — fire/pollution risk","Clean — safe for food/pharma"],
     ["Compressibility","Essentially incompressible","Highly compressible"],
     ["Maintenance","High (seals, oil changes, filters)","Low (simpler system)"],
     ["Cost","High (pump, valves, pipes, tank)","Lower (air compressor only)"],
     ["Best for","Excavators, presses, cranes, lifts","Pick-and-place, packaging, sorting"]],
    cw=[W*0.22,W*0.39,W*0.39]),sp(6),
    p("<b>Applications of Hydraulic Actuators:</b>"),
    b("Excavators, bulldozers, and dump trucks — main working arms."),
    b("Hydraulic presses in metal forming and injection moulding."),
    b("Aircraft landing gear and flight control surfaces."),
    b("Automotive hydraulic brakes and power steering."),
    b("Industrial lifts and scissor jacks."),sp(6),
    tip("Pascal's Law formula is key: F = P × A. Show this in your answer. The comparison table with pneumatic is the most important part — it covers marks for both Q2 and Q3."),sp(12)]

# ─── Q4 ─────────────────────────────────────────────────────────
story += [sec(4,"Solenoid Actuator — Construction, Working, Advantages, Applications"),sp(8)]
story += [
    q("Q4. Explain the construction and working principle of a solenoid actuator. State its advantages, limitations, and applications."),sp(4),
    p("<b>What is a Solenoid?</b>"),
    p("A solenoid is an electromechanical actuator that converts electrical energy directly into a short, straight-line (linear) mechanical motion — either a push or a pull. It works on the principle of electromagnetism: an electric current in a coil creates a magnetic field that moves a metal plunger."),sp(6),
    p("<b>Construction:</b>"),
    b("<b>Coil (Solenoid Winding):</b> A tightly wound coil of insulated copper wire. When current flows through it, it generates a concentrated magnetic field inside the coil."),
    b("<b>Plunger (Armature/Core):</b> A cylindrical rod of soft magnetic material (soft iron) that sits partially inside the coil. This is the moving part."),
    b("<b>Return Spring:</b> A mechanical spring that pushes the plunger back to its original position when the current is switched off."),
    b("<b>Fixed Core (Pole Piece):</b> A stationary piece of magnetic material at one end of the coil that concentrates and strengthens the magnetic field."),
    b("<b>Housing/Frame:</b> Steel frame that provides a low-reluctance magnetic return path and structural support."),sp(6),
    p("<b>Working Principle:</b>"),
    b("<b>When current is switched ON:</b> Current flows through the coil → magnetic field is created → the magnetic field pulls the soft iron plunger into the coil (toward the fixed core) → plunger moves inward → this movement operates a valve, switch, lock, or mechanism."),
    b("<b>When current is switched OFF:</b> Magnetic field disappears → return spring pushes the plunger back to its original (rest) position."),
    b("<b>Force:</b> The pulling force is proportional to the current and the number of coil turns. More current or more turns = stronger pull."),
    f("Force ∝ N × I   (N = number of coil turns, I = current)"),sp(6),
]
story += [ct(["Advantages","Limitations"],
    [["Very fast response — switches in milliseconds","Short stroke only — typically 5 to 50 mm maximum travel"],
     ["Simple, compact, and rugged construction","Force drops off quickly as plunger moves away from centre"],
     ["Direct electrical control — easy to interface with microcontrollers","Generates heat when energized continuously (I²R losses)"],
     ["No mechanical linkage needed — direct push/pull","Only on/off control — not suitable for variable position control"],
     ["Reliable and long service life","Limited force compared to hydraulic/pneumatic at same size"]],
    cw=[W*0.50,W*0.50]),sp(6),
    p("<b>Applications:</b>"),
    b("Solenoid valves — control flow of air, water, or gas in pneumatic and hydraulic systems."),
    b("Door locks and security systems — electric locks in cars and buildings."),
    b("Printer mechanisms — paper feed and ink-head positioning."),
    b("Vending machines and coin mechanisms."),
    b("Automotive fuel injectors — each injector is a small solenoid."),
    b("Relay activation — solenoid coil inside a relay."),sp(6),
    tip("Draw the solenoid with the coil wound around the plunger, the fixed core at the end, and the return spring. Show two states: energized (plunger pulled in) and de-energized (spring pushes out). This sketch gives you easy marks."),sp(12)]

# ─── Q5 ─────────────────────────────────────────────────────────
story += [sec(5,"Relay — Construction, Working, Applications"),sp(8)]
story += [
    q("Q5. What is a relay? Explain the construction and working principle of an electromagnetic relay. List its applications."),sp(4),
    p("<b>What is a Relay?</b>"),
    p("A relay is an electrically operated switch. It uses a small electrical signal (low power) to control a completely separate, much larger electrical circuit (high power). The two circuits are electrically isolated from each other — connected only through the magnetic effect of the relay coil."),sp(6),
    p("<b>Construction:</b>"),
    b("<b>Electromagnetic Coil:</b> A coil of insulated copper wire wound on a soft iron core. When energized, it becomes an electromagnet. This is the input (control) side."),
    b("<b>Soft Iron Core:</b> Increases the magnetic strength of the coil by providing a low-reluctance path for the magnetic flux."),
    b("<b>Armature:</b> A movable flat strip of soft iron pivoted at one end. It sits above the electromagnet and is attracted toward it when the coil is energized."),
    b("<b>Return Spring:</b> Keeps the armature in its original position when the coil is de-energized. This pulls the armature back up."),
    b("<b>Contacts — Fixed and Moving:</b> The switching part. There are three contacts:"),
    b("<b>Common (COM):</b> The terminal always connected to the moving arm."),
    b("<b>Normally Closed (NC):</b> Contact that is CLOSED when the coil is OFF (armature in rest position)."),
    b("<b>Normally Open (NO):</b> Contact that is OPEN when the coil is OFF, and CLOSES when the coil is energized."),sp(6),
    p("<b>Working Principle:</b>"),
    b("<b>Coil OFF (relay at rest):</b> No magnetic field. Armature is held up by the return spring. COM is connected to NC. NO contact is open."),
    b("<b>Coil ON (relay energized):</b> Current flows through coil → electromagnet created → armature is attracted downward toward the core → armature moves → COM disconnects from NC and connects to NO. The high-power circuit is now switched on."),
    b("<b>Coil OFF again:</b> Magnetic field collapses → return spring pulls armature back up → contacts return to original NC state."),
    b("<b>Key advantage:</b> The control circuit (low voltage, e.g. 5V from Arduino) is completely isolated from the load circuit (high voltage, e.g. 230V AC). No direct electrical connection between them."),sp(6),
    p("<b>Applications:</b>"),
    b("Arduino/microcontroller → relay → 230V AC appliance (lights, fan, heater). You've done this!"),
    b("Automotive — starter relay, horn relay, headlight relay."),
    b("Industrial motor control panels — main contactor relays."),
    b("Home appliances — washing machines, refrigerators (compressor switching)."),
    b("Overload protection circuits in electrical panels."),sp(6),
    tip("Draw relay with: coil + iron core on the bottom, armature above it, NC/NO/COM contacts on the right. Show two states — coil OFF (armature up, COM→NC) and coil ON (armature pulled down, COM→NO). This is a guaranteed marks sketch."),sp(12)]

# ─── Q6 ─────────────────────────────────────────────────────────
story += [sec(6,"DC Motor — Construction, Working, Types, Merits, Demerits, Applications"),sp(8)]
story += [
    q("Q6. Explain the construction and working principle of a DC motor. Mention types of DC motors with merits, demerits, and applications."),sp(4),
    p("<b>Construction:</b>"),
    b("<b>Yoke:</b> Cast iron outer frame. Structural support + magnetic return path."),
    b("<b>Field Poles + Pole Shoes:</b> Laminated silicon steel. Create the main magnetic field."),
    b("<b>Field Winding:</b> Insulated copper wire on poles. Carries DC to magnetize the poles."),
    b("<b>Armature Core:</b> Laminated silicon steel disc with slots. Houses armature winding."),
    b("<b>Armature Winding:</b> Insulated copper conductors in slots. Carries load current. Force is generated here (F = BIL)."),
    b("<b>Commutator:</b> Copper segments + mica insulation. Reverses current direction at right moment to maintain continuous torque."),
    b("<b>Brushes:</b> Carbon/graphite blocks. Connect external supply to rotating armature."),sp(6),
    p("<b>Working Principle:</b>"),
    p("When DC is supplied through brushes and commutator to the armature conductors, which sit inside the stator magnetic field, each conductor experiences a Lorentz force F = BIL. Conductors on opposite sides of a coil experience forces in opposite directions — creating a torque that rotates the armature."),
    f("E_b = (Φ × Z × N × P) / (60 × A)   [Back EMF]"),
    f("T_a = 0.159 × (PZ/A) × Φ × I_a     [Armature Torque]"),sp(6),
    p("<b>Types of DC Motors:</b>"),sp(4),
]
story += [ct(["Type","Field connection","Key characteristic","Applications"],
    [["Shunt motor","Field winding in parallel (shunt) with armature. Constant flux.","Constant speed — only 3–5% drop from no-load to full-load. Predictable torque.","Lathes, pumps, fans, conveyors"],
     ["Series motor","Field winding in series with armature. Flux varies with load.","Very high starting torque. Speed drops sharply with load. Must never run without load (dangerous overspeed).","Electric traction, cranes, hoists, EV traction"],
     ["Compound motor","Both series and shunt field windings. Combined behavior.","High starting torque + reasonable speed regulation. Best of both types.","Elevators, rolling mills, printing machines"],
     ["Separately excited","Field winding powered by separate supply. Independent control of field.","Precise, wide-range speed and torque control. Used in servo drives.","Precision drives, Ward-Leonard speed control systems"]],
    cw=[W*0.18,W*0.25,W*0.30,W*0.27]),sp(6),
]
story += [ct(["Merits of DC Motors","Demerits of DC Motors"],
    [["High starting torque available (especially series type)","Brush and commutator wear — requires regular maintenance"],
     ["Easy and smooth speed control by varying voltage or field","Sparking at commutator → EMI, fire risk in volatile environments"],
     ["Good dynamic response — quick to accelerate/decelerate","Heat buildup in rotating armature — difficult to cool"],
     ["Simple control electronics","Not suitable for very high-speed applications without special design"],
     ["Reverse rotation possible by reversing armature current","Relatively heavier and bulkier than equivalent AC motors"]],
    cw=[W*0.50,W*0.50]),sp(6),
    tip("For the shunt motor: flux is constant (parallel = constant V on field). For series motor: starting torque is huge (T ∝ Φ × I_a, and flux also increases with I_a at start). NEVER run a series motor unloaded — it will overspeed and self-destruct."),sp(12)]

# ─── Q7 ─────────────────────────────────────────────────────────
story += [sec(7,"BLDC Motor — Working Principle, Compare with DC Motor"),sp(8)]
story += [
    q("Q7. Describe the working principle of a BLDC motor. Compare it with a conventional DC motor."),sp(4),
    p("<b>Why was BLDC motor developed?</b>"),
    p("The conventional brushed DC motor has three major problems: (1) brushes and commutator wear out mechanically, (2) commutator switching creates electrical sparks and EMI, (3) heat builds up in the rotating armature which is hard to cool. The BLDC motor eliminates all three problems by flipping the design."),sp(6),
    p("<b>Construction — The Flip Design:</b>"),
    b("<b>Stator (fixed, outer part):</b> Contains the 3-phase copper armature windings on a laminated steel core. This is the part that receives electricity. Being on the outside, it can be cooled easily by the motor casing."),
    b("<b>Rotor (rotating, inner part):</b> Contains high-energy permanent magnets (Neodymium). No windings, no brushes required here. Lighter than brushed motor rotor."),
    b("<b>Electronic Speed Controller (ESC) / Inverter:</b> External circuit containing MOSFET switches. Replaces the mechanical commutator. Energizes stator coils in the correct sequence."),sp(6),
    p("<b>Working Principle:</b>"),
    b("The ESC energizes the stator coils in a precise sequence using MOSFET switches."),
    b("This creates a rotating magnetic field in the stator."),
    b("The permanent magnet rotor aligns itself with this rotating field and follows it — producing continuous torque."),
    b("To reverse direction: reverse the switching sequence."),sp(6),
    p("<b>Rotor Position Sensing (How does the controller know which coils to energize?):</b>"),
    b("<b>Hall Effect Sensors (at low/medium speed):</b> Three magnetic sensors placed 120° apart inside the stator. As rotor magnets pass them, they output HIGH/LOW digital signals telling the ESC the exact rotor position."),
    b("<b>Sensorless Back-EMF Method (at high speed):</b> The spinning magnets induce a small back-EMF in the un-energized stator phase. The ESC detects the zero-crossing point of this voltage to determine rotor position without physical sensors."),sp(6),
]
story += [ct(["Feature","Brushed DC Motor","BLDC Motor"],
    [["Commutation","Mechanical (commutator + brushes)","Electronic (MOSFET switches + ESC)"],
     ["Stator","Field magnets / windings","3-phase armature windings"],
     ["Rotor","Armature winding (with commutator)","Permanent magnets (no winding)"],
     ["Maintenance","High — brushes and commutator wear","Very low — no contact parts to wear"],
     ["Sparking/EMI","Yes — commutator switching causes sparks","No sparks — fully electronic switching"],
     ["Efficiency","Lower (brush friction + electrical losses)","Higher (no brush losses)"],
     ["Speed range","Limited by brush/commutator max speed","Very high speeds possible"],
     ["Cooling","Difficult (heat in rotating armature)","Easy (windings on outer, fixed stator)"],
     ["Cost","Low","Higher (permanent magnets + ESC)"],
     ["Applications","Toys, simple automation, low-cost tools","Drones, EVs, high-end fans, robotics"]],
    cw=[W*0.25,W*0.37,W*0.38]),sp(6),
    tip("The key phrase: BLDC flips the conventional design — stator carries current, rotor has magnets. Electronic commutation (MOSFETs) replaces mechanical commutation (brushes+commutator). Hall sensors for low speed, back-EMF for high speed."),sp(12)]

# ─── Q8 ─────────────────────────────────────────────────────────
story += [sec(8,"Stepper Motor — Construction, Types, Working, Advantages, Applications"),sp(8)]
story += [
    q("Q8. Explain construction and working of a stepper motor. Discuss types with advantages, disadvantages, and applications."),sp(4),
    p("<b>Definition:</b>"),
    p("A stepper motor is an electric motor that converts digital electrical pulses into precise, fixed angular steps rather than continuous rotation. Each pulse = exactly one step. This gives it inherent open-loop position control without needing a feedback encoder."),sp(6),
    p("<b>Construction:</b>"),
    b("<b>Stator:</b> Has multiple toothed poles. Each pole is wound with its own coil — each coil is one phase. Energizing a phase creates an electromagnet."),
    b("<b>Rotor:</b> Has evenly spaced teeth made of soft magnetic material (Variable Reluctance type) or permanent magnets (Permanent Magnet type). The teeth count determines the step resolution."),
    b("<b>Phase Windings:</b> Usually 2-phase (bipolar) or 4-phase (unipolar) coil arrangement."),sp(6),
    p("<b>Working Principle:</b>"),
    b("When a stator phase is energized, it creates a localized magnetic field."),
    b("The rotor teeth align with the energized stator pole to minimize magnetic reluctance (closest approach)."),
    b("When the controller switches to the next phase, the rotor rotates by exactly one step to align with the new pole."),
    b("By continuously switching phases in sequence, the rotor steps around the full 360°."),
    f("Step Angle (β) = 360° ÷ (m × Nr)     m = phases, Nr = rotor teeth"),
    p("Example: 4-phase motor, 50 rotor teeth → β = 360° ÷ (4 × 50) = 1.8° per step"),sp(6),
    p("<b>Types of Stepper Motors:</b>"),sp(4),
]
story += [ct(["Type","Rotor material","Key feature","Best for"],
    [["Variable Reluctance (VR)","Soft iron (teethed, no magnets)","Lightest, fastest stepping. Low holding torque. Step angle 5°–15°.","High-speed light-load positioning"],
     ["Permanent Magnet (PM)","Permanent magnets on rotor","Better holding torque. Detent torque when de-energized. Step angle 7.5°–15°.","Consumer electronics, printers"],
     ["Hybrid Stepper","Permanent magnet + toothed soft iron (combines both types)","Best accuracy, highest torque, finest step angle (0.9°–1.8°). Most popular in industry.","CNC machines, 3D printers, robots"]],
    cw=[W*0.22,W*0.22,W*0.33,W*0.23]),sp(6),
]
story += [ct(["Advantages","Disadvantages"],
    [["Open-loop precise positioning — no encoder needed","Torque drops off sharply at high speeds"],
     ["Full holding torque when stationary (coils energized)","Can miss steps (lose position) at resonant frequencies or if overloaded"],
     ["Reliable start, stop, and reverse control","Draws full current even when stationary — low efficiency, heat buildup"],
     ["Step angle is fixed and highly repeatable","Not suitable for very smooth, high-speed continuous rotation"],
     ["Simple interface — just count pulses for position","Generates vibration/noise due to discrete stepping action"]],
    cw=[W*0.50,W*0.50]),sp(6),
    p("<b>Applications:</b>"),
    b("3D printers — all 3 axes (X, Y, Z) driven by stepper motors."),
    b("CNC milling and laser cutting machines — precise tool positioning."),
    b("Computer hard drives — read/write head positioning (older drives)."),
    b("Robotics — joint and gripper positioning in light-duty robots."),
    b("Medical equipment — syringe pumps, dental drills."),
    b("Camera pan/tilt heads, security camera systems."),sp(6),
    tip("Hybrid stepper = most popular in industry. Step angle formula β = 360°/(m×Nr) will be in numericals. Always mention that stepper is OPEN-LOOP — it counts steps for position without a feedback encoder. This is its main advantage AND main risk (can miss steps)."),sp(12)]

# ─── Q9 ─────────────────────────────────────────────────────────
story += [sec(9,"Servo Motor — Construction, Working, Merits, Demerits, Position Control"),sp(8)]
story += [
    q("Q9. Explain construction, working principle, merits and demerits of a servo motor. Why is it preferred for position control?"),sp(4),
    p("<b>What is a Servo Motor?</b>"),
    p("A servo motor is NOT just a motor — it is a complete closed-loop position control system packed into one compact unit. It integrates a primary motor (DC or AC), a reduction gearbox, a position feedback sensor (potentiometer or encoder), and an internal error-correction control circuit — all in one package."),sp(6),
    p("<b>Construction:</b>"),
    b("<b>Primary Motor:</b> Usually a small DC motor (or AC induction motor in industrial servos). Provides the actual rotational power."),
    b("<b>Reduction Gearbox:</b> Multi-stage gear train that reduces motor speed and multiplies torque. Makes the output shaft move slowly with high force."),
    b("<b>Position Sensor (Feedback Element):</b> A potentiometer or optical encoder attached to the output shaft. Continuously measures the actual shaft angle and outputs a proportional electrical signal."),
    b("<b>Internal Control Circuit (Error Amplifier):</b> Compares the target angle (from the PWM command signal) with the actual angle (from the potentiometer). If there is a difference (error), it drives the motor in the correcting direction."),
    b("<b>Output Shaft:</b> The final shaft that connects to the load. Moves to the commanded angle with precision."),sp(6),
    p("<b>Working Principle — Closed Loop Position Control:</b>"),
    b("<b>Step 1 — Command:</b> External controller (e.g. Arduino) sends a PWM signal to the servo."),
    b("<b>Step 2 — Decoding:</b> Internal circuit reads the PWM pulse width and converts it to a target angle. 1ms = 0°, 1.5ms = 90°, 2ms = 180°."),
    b("<b>Step 3 — Compare:</b> The potentiometer reports the current shaft angle. The error amplifier subtracts: Error = Target angle − Actual angle."),
    b("<b>Step 4 — Correct:</b> If error ≠ 0, the motor runs in the direction that reduces the error."),
    b("<b>Step 5 — Hold:</b> When the shaft reaches the target angle, error = 0, motor stops, shaft is held firmly in position."),
    f("[PWM Signal] → [Error Comparator] → [Motor Driver] → [Motor] → [Gearbox] → [Output Shaft]"),
    f("                       ↑ feedback                                                  ↓"),
    f("               [Potentiometer / Encoder] ←──────────────────────────────────────────┘"),sp(6),
    p("<b>Standard 3-Wire Interface:</b>"),
    b("<b>Red wire:</b> +5V or +12V power supply."),
    b("<b>Brown/Black wire:</b> Ground (GND)."),
    b("<b>Orange/Yellow wire:</b> PWM control signal."),sp(6),
]
story += [ct(["Merits","Demerits"],
    [["Highly precise position control — can hold any angle within 1°–2°","Limited range — standard hobby servos only move 0° to 180°"],
     ["Built-in closed-loop feedback — self-correcting, no drift","Higher cost than a simple DC motor of same power"],
     ["High torque at low speed — gearbox multiplies motor torque","Gearbox adds mechanical backlash which limits ultimate precision"],
     ["Compact all-in-one package — easy to integrate","Not suitable for continuous rotation (without modification)"],
     ["Stiff position holding — resists disturbance forces","Position sensor (pot) wears out over millions of cycles"]],
    cw=[W*0.50,W*0.50]),sp(6),
    p("<b>Why are servo motors preferred for position control systems?</b>"),
    b("<b>Closed-loop feedback:</b> The internal potentiometer continuously reports the actual position. The controller always knows where the shaft is and corrects any error automatically."),
    b("<b>High holding stiffness:</b> If an external force tries to push the shaft away from its commanded position, the motor actively resists and returns to the correct angle."),
    b("<b>Precise angle command via PWM:</b> The pulse width directly maps to the output angle — a simple, reliable digital command method."),
    b("<b>Self-contained system:</b> Sensor, controller, gearbox all in one unit — no external components needed for basic position control."),sp(6),
    tip("The servo's biggest advantage over a stepper is CLOSED-LOOP operation — it always knows its actual position and corrects errors. A stepper can lose steps (open-loop). Servo cannot lose position because it checks with the sensor."),sp(12)]

# ─── Q10 ─────────────────────────────────────────────────────────
story += [sec(10,"Selection of Actuators — Industrial and Robotic Applications"),sp(8)]
story += [
    q("Q10. Discuss criteria for selection of actuators for industrial and robotic applications. Consider load, speed, accuracy, power source, and environment."),sp(4),
    p("<b>Introduction:</b>"),
    p("Choosing the right actuator is one of the most important engineering decisions in designing an automation or robotics system. The wrong choice leads to poor performance, high maintenance costs, or safety hazards. The selection is based on a set of technical and operational criteria:"),sp(6),
    p("<b>Criterion 1 — Load / Force Requirements:</b>"),
    b("The actuator must produce enough force or torque to move the intended load with a safety margin (usually 1.5× to 2× the required force)."),
    b("For very heavy loads (tonnes): Hydraulic actuator — highest force density. Example: excavator arm."),
    b("For medium loads: Electrical motor with gearbox or pneumatic cylinder."),
    b("For light, fast tasks: Pneumatic actuator or servo motor."),sp(6),
    p("<b>Criterion 2 — Speed and Response Time:</b>"),
    b("Pneumatic actuators have the fastest response (air moves quickly at low viscosity). Best for fast on/off tasks."),
    b("Electrical actuators (BLDC, servo) offer high speed AND controllable speed — best for variable-speed tasks."),
    b("Hydraulic actuators are slower due to oil viscosity but very powerful."),
    b("Stepper motors are good for slow, precise positioning but slow at high loads."),sp(6),
    p("<b>Criterion 3 — Accuracy and Repeatability:</b>"),
    b("Servo motors: highest precision — closed-loop with encoder. Best for robotic joints and CNC axes."),
    b("Stepper motors: good precision — open-loop step counting. Good for 3D printers and plotters."),
    b("Hydraulic: very precise for heavy loads (oil incompressible). Used in aircraft controls."),
    b("Pneumatic: least precise — air compresses, giving a spongy, imprecise feel. Not good for fine positioning."),sp(6),
    p("<b>Criterion 4 — Available Power Source:</b>"),
    b("Pneumatic: requires compressed air infrastructure (compressor, dryer, piping). Not practical in remote locations."),
    b("Hydraulic: requires hydraulic pump, oil reservoir, piping. Complex to install."),
    b("Electrical: only needs electrical supply (often already available). Most practical for most locations."),
    b("Battery-powered systems (robots, drones): must use electrical actuators — pneumatic/hydraulic impractical."),sp(6),
    p("<b>Criterion 5 — Environment:</b>"),
    b("Clean rooms (food/pharma/semiconductor): Pneumatic or enclosed electrical actuators. NO hydraulic (oil contamination risk)."),
    b("Hazardous/explosive environments: Pneumatic (no sparks). Electrical motors need ATEX certification."),
    b("High temperature: Hydraulic and pneumatic handle heat better than standard electrical motors."),
    b("Outdoor/wet environments: Electrical actuators with high IP rating (IP67, IP68). Hydraulic also handles moisture well."),
    b("High vibration/shock: Hydraulic handles shock loads well. Servo motors can be damaged by excessive shock."),sp(6),
    p("<b>Criterion 6 — Maintenance and Running Costs:</b>"),
    b("Pneumatic: low maintenance (simple valves and cylinders). Compressor needs regular service."),
    b("Hydraulic: high maintenance (oil changes, seal replacements, filter cleaning, leak checks)."),
    b("Brushed DC motor: medium (brush and commutator replacement every 1000–5000 hours)."),
    b("BLDC/Servo/Stepper: low maintenance (no brushes or commutator). Long service life."),sp(6),
]
story += [ct(["Criterion","Pneumatic","Hydraulic","Electrical (Servo/BLDC)"],
    [["Force/Load","Low–medium","Extremely high","Medium–high"],
     ["Speed","Very fast","Slow–medium","Fast, controllable"],
     ["Accuracy","Low (air compresses)","High","Very high (closed-loop)"],
     ["Power source","Air compressor","Hydraulic pump+oil","Electrical supply"],
     ["Environment","Clean, food-safe","Risk of leaks","Clean, needs IP rating"],
     ["Maintenance","Low","High","Low (brushless)"],
     ["Cost","Low","High","Medium–high"],
     ["Best for","Packaging, sorting","Cranes, presses","Robots, CNC, automation"]],
    cw=[W*0.22,W*0.20,W*0.20,W*0.38]),sp(6),
    p("<b>Summary Rule of Thumb:</b>"),
    b("Need massive force → Hydraulic."),
    b("Need fast, clean, simple on/off motion → Pneumatic."),
    b("Need precision, programmability, variable control → Electrical (servo for position, BLDC for speed, stepper for step-count positioning)."),sp(6),
    tip("For a 10-mark question cover all 6 criteria with one actuator recommendation per criterion. The summary table and the 3-rule thumb at the end show you understand the practical decision-making process — which is exactly what the examiner wants."),sp(14)]

# ─── Summary ─────────────────────────────────────────────────────
sdata=[[Paragraph("<b>Quick Recall — All 10 Questions</b>",
         S("fh",fontName="Helvetica-Bold",fontSize=11,textColor=C_HEAD,leading=14))]]
for it in [
    "Q1: Actuator = energy → motion. Pneumatic=air/fast, Hydraulic=oil/heavy, Electrical=precise.",
    "Q2: Pneumatic cylinder — piston, rod, barrel, 2 ports. Double-acting: air both ways. Fast, clean, limited force.",
    "Q3: Hydraulic — Pascal's Law (F=P×A). Oil incompressible = precise + powerful. Risk of leaks.",
    "Q4: Solenoid — coil + plunger + spring. Current ON → plunger pulls in. Current OFF → spring returns. Fast, short stroke only.",
    "Q5: Relay — coil + armature + NC/NO contacts. Low-power signal controls high-power circuit. Electrically isolated.",
    "Q6: DC motor — F=BIL makes rotor spin. Shunt=constant speed. Series=high starting torque (never unloaded!). Compound=both.",
    "Q7: BLDC — flip design. Windings on stator, magnets on rotor. Electronic commutation. Hall sensors or Back-EMF for position.",
    "Q8: Stepper — one pulse = one step. β=360°/(m×Nr). Open-loop. Hybrid type = most popular. Torque drops at high speed.",
    "Q9: Servo = motor+gearbox+potentiometer+control circuit. PWM: 1ms=0°, 1.5ms=90°, 2ms=180°. Closed-loop = always self-corrects.",
    "Q10: Selection criteria: Load→Hydraulic for heavy. Speed→Pneumatic fastest. Precision→Servo/BLDC. Clean room→Pneumatic/Electrical. Battery→Electrical only.",
]:
    sdata.append([Paragraph(f"• {it}",
        S("fi",fontName="Helvetica",fontSize=9.5,textColor=C_DARK,leading=14))])

st=Table(sdata,colWidths=[W])
st.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),C_LIGHT),
    ("BACKGROUND",(0,1),(-1,-1),colors.white),("GRID",(0,0),(-1,-1),0.5,C_RULE),
    ("TOPPADDING",(0,0),(-1,-1),6),("BOTTOMPADDING",(0,0),(-1,-1),6),
    ("LEFTPADDING",(0,0),(-1,-1),10)]))
story.append(st)

doc.build(story)
print(f"Done → {OUTPUT}")