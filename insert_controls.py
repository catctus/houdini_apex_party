"""
This apex script component helps add secondary and offset controls to an already defined transform.
Pretty common operation. 

I added the header and footer, but could just be deleted, and use header + template as component
"""
HoudiniVersion("21.0.440")
rigname: String = BindInput()
character: Geometry = BindInput()
graph: ApexGraphHandle = BindInput(rig=ApexGraphHandle())
bypass: Bool = BindInput()
rigname, graph = character.getRig(graph_name=rigname, graph=graph, bypass=bypass)
##### header end #####
# we want to make this into a subgraph
def AddControl(graph: ApexGraphHandle, 
               guides: Geometry,
               name: String,
               match: String = "",
               parent: String = "",
               promote: String = "t r s", 
               shapescale: Vector3 = Vector3(1,1,1),
               shape: String = "cross_wires",
               shapeColor: Vector3 = Vector3(0,1,0),
               shapeTranslate: Vector3 = Vector3(0,0,0),
               shapeRotate: Vector3 = Vector3(0,0,0),
               shapeScale: Vector3 = Vector3(10,10,10),
               translateOffset: Vector3 = Vector3(0,0,0),
               rotateOffset: Vector3 = Vector3(0,0,0),
               scaleOffset: Vector3 = Vector3(1,1,1),
               offsetMode: Int = 0,
               rotateOrder: Int = 0,
               scaleInheritance: Int=0,
               transformOrder: Int = 0,
               overrideControl: Bool = True,
               setShapeData: Bool = True,
               tags: StringArray=[])->tuple[ApexGraphHandle, Geometry, ApexNodeID]:
    
    matchname = rkutil.FirstNodeNameFromPattern(graph, match)
    
    
    if matchname == "":
        matchxform:Matrix4 = value(); 
    else:
        matchxform:Matrix4 = guides.GetPointTransform(matchname)
    
    offsetxform = apex.transform.build(translateOffset, rotateOffset, scaleOffset)
    
    xform, overridexform = rktrf.AddOffsets(matchxform, offsetxform)
    
    ctrlxform, ctrlpt, ctrname = guides.FindOrAddGuide(name=name,
                                                       xform=xform,
                                                       scaleinheritance=scaleInheritance,
                                                       rord=rotateOrder,
                                                       parent=parent,
                                                       promote=promote,
                                                       shape=shape,
                                                       shapetranslate=shapeTranslate,
                                                       shaperotate=shapeRotate,
                                                       shapescale=shapeScale,
                                                       shapecolor=shapeColor,
                                                       overridecontrol=overrideControl,
                                                       setshapedata=setShapeData,
                                                       tags=tags
                                                       )
    
    guides.updateJoint(ptnum=ctrlpt, name=ctrname, xform=ctrlxform)
    
    pattern = f"@name={ctrname}"
    guides, nodeids = graph.controlsFromGuides(geo=guides, group=pattern)
    
    control : ApexNodeID = nodeids[0]
    
    return graph, guides, control

def AddConstraint(graph : ApexGraphHandle,
                  guides : Geometry,
                  driver: String,
                  driven: String,
                  components: Int = 7,
                  ignoreoffset: Bool = False,
                  parentConstraint: Bool = True
                  ):
                  
    driverName = rkutil.FirstNodeNameFromPattern(graph, driver)
    drivenName = rkutil.FirstNodeNameFromPattern(graph, driven)
    
    driverNode = graph.FindNode(driverName)
    drivenNode = graph.FindNode(drivenName)    
    
    constraintNode = drivenNode
    # this will keep the transform intact
    if parentConstraint:
        reset: Matrix4 = value()
        drivenJnt = guides.findJoint(drivenName)
        originalNodeParentPt = guides.getParent(drivenJnt)
        originalNodeParentName = guides.jointData(originalNodeParentPt)
        
        
        constraintName = f"{driverName}_{drivenName}_parentConstraint"
        
        # add a parent transform
        guides, constraintNode = graph.AddControl(guides, 
                                           constraintName,
                                           match=drivenName,
                                           promote="", 
                                           parent=originalNodeParentName)
                                                                        
        constraintNode.xform_out.connect(drivenNode.parent_in)
        constraintNode.localxform_out.connect(drivenNode.parentlocal_in)
        drivenNode.updateNode(parms={'restlocal':reset})
    
    driverXForm = guides.getPointTransform(driverName)
    drivenXForm = guides.getPointTransform(drivenName)
    ingnore_offset_xform = twoWaySwitch(drivenXForm, driverXForm, ignoreoffset)
    
    parentblend_parms = {'newparent_bind':driverXForm, 
                         'parent_bind':ingnore_offset_xform, 'parent':ingnore_offset_xform,
                         'blend':1.0, 'components':components}
                         
    transformBlendName = f'{driverName}_{drivenName}_TransformDriverBlend'
    parentBlend = graph.addOrUpdateNode(name=transformBlendName, callback='rig::ParentBlend',
                                        parms=parentblend_parms)
    parentBlend.parent_out.connect(constraintNode.xform_in)
    driverNode.xform_out.connect(parentBlend.newparent_in)



    return graph, guides
"""
# constraint
def AddConstraints(graph: ApexGraphHandle, 
                   guides: Geometry, 
                   drivernode: ApexNodeID, 
                   drivername: String, 
                   driven: String, 
                   components: Int,  
                   ingnoreoffset: Bool, 
                   drivenoffsetctrls: Bool,
                   parentconstaint: Bool):
                   
        
        nodes = graph.findNodes(f'{driven} - {drivername}')
        driverxform = guides.getPointTransform(drivername)
        
        for node in nodes:
            
            drivenname = node.name()
            
            if drivenoffsetctrls:
                guides, drivenname, drivernode, driverxform = graph.AddConstraintControls(guides=guides, name=drivenname, 
                                                                                          driver=drivername, node=node, 
                                                                                          promote=True, parent=drivername)
            
            if parentconstaint:
                original_node = node
                reset: Matrix4 = value()
                drivenjnt = guides.findJoint(drivenname)
                originalnodeparentpt = guides.getParent(drivenjnt)
                originalnodeparentname = guides.jointData(originalnodeparentpt)
                
                guides, drivenname, node = graph.AddConstraintControls(guides=guides, name=drivenname, 
                                                                       driver=drivername, node=node, 
                                                                       promote=False, parent=originalnodeparentname)
                node.xform_out.connect(original_node.parent_in)
                node.localxform_out.connect(original_node.parentlocal_in)
                original_node.updateNode(parms={'restlocal':reset})
                
                
            drivenxform = guides.getPointTransform(drivenname)
            ingnore_offset_xform = twoWaySwitch(drivenxform, driverxform, ingnoreoffset)
            
            parentblend_parms = {'newparent_bind':driverxform, 
                                 'parent_bind':ingnore_offset_xform, 'parent':ingnore_offset_xform,
                                 'blend':1.0, 'components':components}
            drivenname = f'{drivenname}_TransformDriverBlend'
            parentblend = graph.addOrUpdateNode(name=drivenname, callback='rig::ParentBlend',
                                                parms=parentblend_parms)
            parentblend.parent_out.connect(node.xform_in)
            drivernode.xform_out.connect(parentblend.newparent_in)



        return graph, guides
"""
def BuildControl(graph:ApexGraphHandle, 
                 guides:Geometry, 
                 guideTarget:ApexNodeID, 
                 name:String,
                 parent:String = "",      
                 buildSecondaryCtr:Bool=True,
                 buildOffsetCtr:Bool=True,
                 controlSuffix:String="ctr",
                 offsetSuffix:String="offset",
                 secondarySuffix:String="secondary")->tuple[ApexGraphHandle, Geometry]:
    
    guidename :String = guideTarget.name()
    guideparent : ApexNodeID = graph.GetTransformParent(guideTarget)
    guideparentname : String = guideparent.name()
    pos = guides.getPointTransform(name=guidename)
    
    if buildOffsetCtr:
        guides, offsetCtr = graph.AddControl(guides, f"{name}_{offsetSuffix}_{controlSuffix}", match=guidename, parent=parent)
        parent = offsetCtr.name()
    
    # create the main control
    guides, mainctr = graph.AddControl(guides, f"{name}_{controlSuffix}", match=guidename, parent=parent)
    driver : String =mainctr.name()
    
    # create the secondary controls
    if buildSecondaryCtr:
        guides, secctr = graph.AddControl(guides, f"{name}_{secondarySuffix}_{controlSuffix}", match=guidename, parent=mainctr.name())        
        driver=secctr.name()
        
    guides = graph.AddConstraint(guides, driver, guidename)
    
    return graph, guides

    
def AddControlsMulti(graph:ApexGraphHandle, guides:Geometry, setups: DictArray)->tuple[ApexGraphHandle, Geometry]:

    for s in setups:
        guide : String = s["guideTarget#"]
        useGuideName : Bool = s["useGuideName#"]
        customName : String = s["customControlName#"]
        controlParent : String = s["controlParent#"]
        useGuideTargetParent : Bool = s["useGuideTargetParent#"]
        buildSecondaryCtr : Bool = s["buildSecondary#"]
        buildOffsetCtr : Bool = s["buildOffset#"]
        # to find nodes based on tag
        nodes:ApexNodeIDArray = graph.FindNodes(graph=graph,
                                                pattern=guide)
        
        for i, node in enumerate(nodes):
            name : String = node.name()
            # check if we are using custom name, in that case update
            if not useGuideName:
                if len(nodes)>1:
                    name = f"{customName}_{i}"
                else:
                    name = customName
            
            if useGuideTargetParent:
                controlParentNode = graph.GetTransformParent(node)
                controlParent = controlParentNode.name()
            
            
            #buildControl(graph:ApexGraphHandle, guides:Geometry, guideTarget: ApexNodeID, name:String)
            guides = graph.buildControl(guides=guides, 
                                        guideTarget=node, 
                                        name=name, 
                                        parent=controlParent,
                                        buildSecondaryCtr=buildSecondaryCtr,
                                        buildOffsetCtr=buildOffsetCtr)

    
    graph.layout()
    return graph, guides


setups = bindMultiparm()

# control build
addToMultiparm(setups, "guideTarget", "", preset_kwargs ={"prompt_text":"name/pattern/tag", "label":"Guide Target(s)"})

addToMultiparm(setups, "useGuideTargetParent", True, preset_kwargs ={"joins_with_next":1})
addToMultiparm(setups, "controlParent", "", preset_kwargs ={"prompt_text":"Parent To", 
                                                            "disable_when":'{useGuideTargetParent# == 1}'})
                                                            
addToMultiparm(setups, "useGuideName", True, preset_kwargs={'joins_with_next':1})
addToMultiparm(setups, "customControlName", "", preset_kwargs ={"prompt_text":"name_<controlPrefix>", "disable_when":'{useGuideName# == 1}'})
addToMultiparm(setups, "buildSecondary", True, preset_kwargs={'joins_with_next':1})
addToMultiparm(setups, "buildOffset", False, preset_kwargs={'joins_with_next':1})

addToMultiparm(setups, "controlShape", "cross_wires", preset_kwargs={'joins_with_next':1})
addToMultiparm(setups, "secondaryControlShape", "cross_wires", preset_kwargs={'joins_with_next':1})
addToMultiparm(setups, "offsetControlShape", "cross_wires", preset_kwargs={'joins_with_next':1})
# might have to fix this one
addToMultiparm(setups, "_shapeReference", "cross_wires", preset='controlshapes')

addToFolder("ControlSetup", ["guideTarget#", "useGuideTargetParent#", "controlParent#", "useGuideName#", 
                             "customControlName#", "buildSecondary#", 
                             "buildOffset#"], parent="setups")

addToFolder("ControlShapes", ["controlShape#", "offsetControlShape#", 
                             "parentControlShape#", "_shapeReference#"], parent="setups")
                             
#! add parent or use target parent


# settings
controlSuffix : String = bindInput("ctr",preset_kwargs={'joins_with_next':1})
offsetSuffix : String = bindInput("offset",preset_kwargs={'joins_with_next':1})
secondarySuffix : String = bindInput("secondary")
guidesource: String = bindInput("Guides.skel")


addToFolder("Build", [setups])
addToFolder("Settings", [controlSuffix, offsetSuffix, secondarySuffix, guidesource])


#Setup
guides : Geometry = character.findCharacterElement(guidesource)
guides = graph.AddControlsMulti(guides=guides, setups=setups)
character.updateCharacterElement(guidesource, guides)



### footer end
character.updateRig(graph_name=rigname, graph=graph, bypass=bypass)
BindOutput(character)
BindOutput(rig=graph)

