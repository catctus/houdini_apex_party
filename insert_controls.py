def add_extra_controls(graph: ApexGraphHandle, 
                       #guides: Geometry,
                       target: String,
                       trf_pos: Int,
                       after_prefix: String,
                       before_prefix: String,
                       promote_t: Bool,
                       promote_r: Bool,
                       promote_s: Bool):
    
    # gather data
    target_node = graph.findNode(target)
    parent_node = graph.GetTransformParent(target_node)
    children_node_array = graph.GetTransformChildren(target_node)
    
    new_controls : ApexNodeIDArray = []
    # if we building an after control (or both)
    if trf_pos == 0 or trf_pos==2:
        beforeCtrl = graph.addNode(f"{target}{after_prefix}", callback="TransformObject")
        if promote_t:
            beforeCtrl.t_in.promote(f"{target}{after_prefix}_t")
            beforeCtrl.r_in.promote(f"{target}{after_prefix}_r")
            beforeCtrl.s_in.promote(f"{target}{after_prefix}_s")
        
        target_node.xform_out.connect(beforeCtrl.parent_in)
        
        new_controls.append(beforeCtrl)
        
        #graph.UpdateNodeProperties(beforeCtrl, {"shapetype":"wirebox"})
        #graph.ControlShape()
        #graph.AddSetPointTransforms("pointtransform", [beforeCtrl], srcport="xform")
        
        
        #apex.sek.GetPointTransforms(geo=guides, name=f"{target}{after_prefix}")
        #beforeCtrl.parent.connect(target_node.xform)
    graph.AddSetPointTransforms("pointtransform", new_controls, srcport="xform")
    
    
    
    return graph

# create a bind multiparam
add_controls = bindMultiparm(preset_kwargs={"label":"test"})

addToMultiparm(add_controls, "TargetControlName", "")
addToMultiparm(add_controls, "NewTransformPosition", 0, 
               preset='menu',
               preset_kwargs={'menu_labels':['after', 'before', 'both'],
                              'menu_items':[0,1,2]})
addToMultiparm(add_controls, "PrefixAfterControl", "_secondary",preset_kwargs={'joins_with_next':1})
addToMultiparm(add_controls, "PrefixBeforeControl", "_offset", preset_kwargs={"disable_when":"{NewTransformPosition==2}"})

# could maybe split this up as well.. 
addToMultiparm(add_controls, "PromoteT", True, preset_kwargs={'joins_with_next':1})
addToMultiparm(add_controls, "PromoteR", True, preset_kwargs={'joins_with_next':1})
addToMultiparm(add_controls, "PromoteS", False)

# Get guide geo
#guidesource: String = BindInput()
#_, guides, _ = FindCharacterElement(character=character, primpath=guidesource)


for ctrl in add_controls:
    target_ctrl_name : String = ctrl["TargetControlName#"]
    trf_pos : Int = ctrl["NewTransformPosition#"]
    after_prefix : String = ctrl["PrefixAfterControl#"]
    before_prefix : String = ctrl["PrefixBeforeControl#"]
    promote_t : Bool = ctrl["PromoteT#"]
    promote_r : Bool = ctrl["PromoteR#"]
    promote_s : Bool = ctrl["PromoteS#"]
    
    if not bypass:
        graph = add_extra_controls(graph, 
                                    #guides,
                               target_ctrl_name,
                               trf_pos,
                               after_prefix, 
                               before_prefix,
                               promote_t,
                               promote_r,
                               promote_s)
