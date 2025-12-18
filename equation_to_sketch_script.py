# Fusion script to generate cycloid profile. Made mostly by gemini 3.0
import adsk.core, adsk.fusion, traceback
import math 

def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui  = app.userInterface
        design = app.activeProduct
        
        if not design:
            ui.messageBox('No active Fusion design found.')
            return

        # --- 1. LOAD FUSION PARAMETERS ---
        param_context = {}
        for param in design.allParameters:
            # param.value is always in internal units (cm for length, radians for angles, unitless for counts)
            param_context[param.name] = param.value

        # --- 2. GET USER INPUTS ---
        
        # We pre-fill the boxes with your specific equations for convenience
        default_x = "(D/2)*cos(t)-(d/2)*cos(t+arctan((sin((Nr_Rollers-1)*t))/(cos((Nr_Rollers-1)*t)-D/(2*excentricity*Nr_Rollers))))-excentricity*cos(Nr_Rollers*t)"
        default_y = "(-D/2)*sin(t)+(d/2)*sin(t+arctan((sin((Nr_Rollers-1)*t))/(cos((Nr_Rollers-1)*t)-D/(2*excentricity*Nr_Rollers))))+excentricity*sin(Nr_Rollers*t)"

        (x_eqn, cancelled) = ui.inputBox("Enter X equation:", "X Equation", default_x)
        if cancelled: return

        (y_eqn, cancelled) = ui.inputBox("Enter Y equation:", "Y Equation", default_y)
        if cancelled: return

        (t_start_str, cancelled) = ui.inputBox("Enter t start:", "T Start", "0")
        if cancelled: return
        (t_end_str, cancelled) = ui.inputBox("Enter t end (2*pi):", "T End", "6.282")
        if cancelled: return

        try:
            t_start = float(t_start_str)
            t_end = float(t_end_str)
        except ValueError:
            ui.messageBox("Invalid number for T range.")
            return

        # --- 3. SELECT PLANE ---
        selection = ui.selectEntity('Select a plane for the sketch', 'ConstructionPlanes,PlanarFaces')
        if not selection: return
        selected_plane = selection.entity

        # --- 4. GENERATE POINTS ---
        num_steps = 160  # Increased resolution for cycloidal curves
        points = adsk.core.ObjectCollection.create()
        
        # Create Math Context
        eval_context = math.__dict__.copy()
        
        # Add Fusion Parameters
        eval_context.update(param_context)
        
        # --- FIX: Map 'arctan' to 'atan' so your equation works ---
        eval_context['arctan'] = math.atan

        step_size = (t_end - t_start) / num_steps

        for i in range(num_steps + 1):
            t = t_start + (i * step_size)
            eval_context['t'] = t
            
            try:
                x = eval(x_eqn, {"__builtins__": None}, eval_context)
                y = eval(y_eqn, {"__builtins__": None}, eval_context)
                points.add(adsk.core.Point3D.create(x, y, 0))
            except ZeroDivisionError:
                # Skip points where denominator is 0 (common in some complex curves)
                continue 
            except Exception as e:
                ui.messageBox(f"Error at t={t:.2f}.\nDetails: {e}")
                return

        # --- 5. DRAW SKETCH ---
        root = design.rootComponent
        sketch = root.sketches.add(selected_plane)
        
        # Splines can fail if points are too close or identical; usually fine here
        if points.count > 1:
            sketch.sketchCurves.sketchFittedSplines.add(points)
        else:
            ui.messageBox("Not enough valid points generated.")

    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

"""
X = (D/2) * cos(phi) - (d/2) * cos(phi+yps) - e * cos(N*phi)
Y = (-D/2) * sin(phi) + (d/2) * sin(phi+yps) + e * sin(N*phi)

D = 100  # Pitch diameter rollers
d = 10  # roller diameter
N = 10  # nr of rollers
e = 5  # eccentricity
# phi = t, between 0 --> 2pi-0.001
yps = arctan( (sin( (N-1) * phi)) / ( cos( (N-1) *phi ) - D/(2*e*N) ) )


(D/2)*cos(t)-(d/2)*cos(t+arctan((sin((Nr_Rollers-1)*t))/(cos((Nr_Rollers-1)*t)-D/(2*excentricity*Nr_Rollers))))-excentricity*cos(Nr_Rollers*t)
(-D/2) * sin(t) + (d/2) * sin(t+arctan( (sin( (Nr_Rollers-1) * t)) / ( cos( (Nr_Rollers-1) *t ) - D/(2*excentricity*Nr_Rollers) ) )) + excentricity * sin(Nr_Rollers*t)

"""
