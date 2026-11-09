using System;
using System.IO;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.SceneManagement;
using UnityEditor;
using UnityEditor.SceneManagement;

public static class TerrainLevelsBuilder {
    static bool pipeline;
    const string Root="Assets/TerrainLevels/";
    static string Project{get{return Directory.GetParent(Application.dataPath).FullName;}}
    public static Mesh LoadMesh(string input,string output){
        Mesh mesh=new Mesh{name=Path.GetFileNameWithoutExtension(input),indexFormat=IndexFormat.UInt32};
        using(var b=new BinaryReader(File.OpenRead(input))){
            int n=b.ReadInt32(),ni=b.ReadInt32();var v=new Vector3[n];var normal=new Vector3[n];var uv=new Vector2[n];var idx=new int[ni];
            for(int i=0;i<n;i++)v[i]=new Vector3(b.ReadSingle(),b.ReadSingle(),b.ReadSingle());
            for(int i=0;i<n;i++)normal[i]=new Vector3(b.ReadSingle(),b.ReadSingle(),b.ReadSingle());
            for(int i=0;i<n;i++)uv[i]=new Vector2(b.ReadSingle(),b.ReadSingle());
            for(int i=0;i<ni;i++)idx[i]=b.ReadInt32();mesh.vertices=v;mesh.normals=normal;mesh.uv=uv;mesh.triangles=idx;mesh.RecalculateBounds();mesh.RecalculateTangents();
        }
        var prior=AssetDatabase.LoadAssetAtPath<Mesh>(output);
        if(prior!=null){EditorUtility.CopySerialized(mesh,prior);UnityEngine.Object.DestroyImmediate(mesh);return prior;}
        AssetDatabase.CreateAsset(mesh,output);return mesh;
    }
    static Material Save(Material m,string path){var old=AssetDatabase.LoadAssetAtPath<Material>(path);if(old!=null){EditorUtility.CopySerialized(m,old);UnityEngine.Object.DestroyImmediate(m);return old;}AssetDatabase.CreateAsset(m,path);return m;}
    [MenuItem("Lunar Levels/Rebuild twenty-four scenes")]
    public static void Build(){
        try{
            AssetDatabase.Refresh();Directory.CreateDirectory("Assets/LevelScenes");Directory.CreateDirectory(Path.Combine(Project,"Outputs","LevelVerification"));
            var config=AssetDatabase.LoadAssetAtPath<TextAsset>(Root+"levels_config.json");var all=JsonUtility.FromJson<DemoConfiguration>(config.text);var metadata=JsonUtility.FromJson<LevelConfig>(config.text);
            var scenePaths=new List<string>();
            for(int sceneIndex=0;sceneIndex<all.scenes.Length;sceneIndex++){
            var c=all.scenes[sceneIndex];EditorSceneManager.NewScene(NewSceneSetup.EmptyScene,NewSceneMode.Single);
            PlayerSettings.colorSpace=ColorSpace.Linear;PlayerSettings.productName="Lunar Terrain Three Levels";PlayerSettings.defaultScreenWidth=1600;PlayerSettings.defaultScreenHeight=900;PlayerSettings.fullScreenMode=FullScreenMode.Windowed;PlayerSettings.runInBackground=true;
            QualitySettings.antiAliasing=4;QualitySettings.shadows=ShadowQuality.All;QualitySettings.shadowDistance=150;QualitySettings.shadowResolution=ShadowResolution.VeryHigh;QualitySettings.shadowCascades=4;
            RenderSettings.skybox=null;RenderSettings.ambientMode=AmbientMode.Flat;RenderSettings.ambientLight=Color.white*.10f;RenderSettings.fog=false;
            var mat=Save(new Material(AssetDatabase.LoadAssetAtPath<Material>("Assets/LunarPilot/Generated/"+c.source+"_mixed.mat")){name=c.id+" regolith"},Root+"Materials/"+c.id+"_regolith.mat");
            Vector4 offset=mat.GetVector("_Offset");offset.x+=metadata.scenes[sceneIndex].sourceOrigin[0];offset.y+=metadata.scenes[sceneIndex].sourceOrigin[1];mat.SetVector("_Offset",offset);mat.SetFloat("_Strength",.40f);
            var clay=new Material(Shader.Find("Standard")){name="Shape inspection"};clay.color=new Color(.48f,.47f,.44f);clay.SetFloat("_Glossiness",.05f);clay=Save(clay,Root+"Materials/clay.mat");
            var mesh=LoadMesh(Root+c.mesh,Root+"Meshes/"+c.id+"_surface.asset");
            var ground=new GameObject("Single continuous terrain - near field and distant context");ground.layer=8;ground.AddComponent<MeshFilter>().sharedMesh=mesh;var renderer=ground.AddComponent<MeshRenderer>();renderer.sharedMaterial=mat;renderer.shadowCastingMode=ShadowCastingMode.On;renderer.receiveShadows=true;
            var terrainCollider=ground.AddComponent<MeshCollider>();terrainCollider.cookingOptions=MeshColliderCookingOptions.CookForFasterSimulation|MeshColliderCookingOptions.EnableMeshCleaning|MeshColliderCookingOptions.WeldColocatedVertices;terrainCollider.sharedMesh=mesh;
            var targetMat=new Material(Shader.Find("OcclusionDemo/Target")){name="Fixed red target"};targetMat.SetColor("_Color",Color.red);targetMat.SetColor("_SegmentationColor",Color.white);targetMat=Save(targetMat,Root+"Materials/target.mat");
            var target=GameObject.CreatePrimitive(PrimitiveType.Sphere);target.name="Fixed red target";target.layer=11;target.transform.position=OcclusionDemo.V(c.targetPosition);target.transform.localScale=Vector3.one*c.targetRadius*2;target.GetComponent<Renderer>().sharedMaterial=targetMat;UnityEngine.Object.DestroyImmediate(target.GetComponent<Collider>());
            var sun=new GameObject("Sun").AddComponent<Light>();sun.type=LightType.Directional;sun.intensity=1.2f;sun.color=new Color(1,.988f,.962f);sun.shadows=LightShadows.Soft;sun.shadowBias=.12f;sun.shadowNormalBias=.5f;sun.shadowResolution=LightShadowResolution.VeryHigh;
            sun.transform.rotation=Quaternion.LookRotation(-new Vector3(-.62f,.91f,.48f),Vector3.up);
            var cam=new GameObject("Main Camera").AddComponent<Camera>();cam.tag="MainCamera";cam.clearFlags=CameraClearFlags.SolidColor;cam.backgroundColor=Color.black;cam.nearClipPlane=.025f;cam.farClipPlane=5000;cam.fieldOfView=66;cam.allowHDR=true;cam.allowMSAA=true;
            var tone=cam.gameObject.AddComponent<LunarToneEffect>();tone.toneShader=Shader.Find("LunarPilot/ACES");tone.exposure=.9f;
            var controller=cam.gameObject.AddComponent<CharacterController>();cam.gameObject.layer=10;controller.height=1;controller.radius=.18f;controller.center=new Vector3(0,-.1f,0);controller.stepOffset=.18f;controller.slopeLimit=35;controller.skinWidth=.025f;controller.enabled=false;
            var demo=new GameObject("Revision route data").AddComponent<OcclusionDemo>();demo.enabled=false;demo.configuration=config;demo.heightMap=AssetDatabase.LoadAssetAtPath<TextAsset>(Root+c.heightData);demo.sceneIndex=sceneIndex;demo.viewCamera=cam;demo.target=target.transform;demo.ground=renderer;demo.materialOptions=new[]{clay,mat};demo.EnsureData();
            var routeMat=Save(new Material(Shader.Find("Unlit/Color")){color=new Color(.2f,.65f,.77f)},Root+"Materials/route.mat");var line=new GameObject("Overview camera route").AddComponent<LineRenderer>();line.sharedMaterial=routeMat;line.positionCount=c.route.Length;line.startWidth=line.endWidth=.08f;
            for(int i=0;i<c.route.Length;i++){Vector3 p=OcclusionDemo.V(c.route[i].position);p.y=demo.Height(p.x,p.z)+.06f;line.SetPosition(i,p);}line.enabled=false;demo.routeLine=line;
            var rockRoot=new GameObject("Static embedded source rocks");foreach(var rec in c.rocks){
                var rockMesh=AssetDatabase.LoadAssetAtPath<Mesh>("Assets/OcclusionDemo/Meshes/rock_"+rec.type+".asset");var rock=new GameObject("Embedded rock");rock.transform.SetParent(rockRoot.transform);rock.transform.rotation=Quaternion.Euler(0,rec.yaw,0);Vector3 scale=OcclusionDemo.V(rec.stretch)*rec.scale;rock.transform.localScale=scale;float height=rockMesh.bounds.size.y*scale.y;
                rock.transform.position=new Vector3(rec.x,rec.ground-rockMesh.bounds.min.y*scale.y-height*rec.burial,rec.z);rock.AddComponent<MeshFilter>().sharedMesh=rockMesh;rock.AddComponent<MeshRenderer>().sharedMaterial=AssetDatabase.LoadAssetAtPath<Material>("Assets/LunarPilot/Generated/rock_"+rec.type+".mat");
                var visual=new GameObject("Exact visual occluder");visual.transform.SetParent(rock.transform,false);visual.layer=9;visual.AddComponent<MeshCollider>().sharedMesh=rockMesh;
                var contact=new GameObject("Inset contact surface");contact.transform.SetParent(rock.transform,false);contact.layer=8;contact.transform.localPosition=rockMesh.bounds.center*.08f;contact.transform.localScale=Vector3.one*.92f;contact.AddComponent<MeshCollider>().sharedMesh=rockMesh;
            }
            Physics.IgnoreLayerCollision(10,9,true);
            var revision=new GameObject("Terrain review controls").AddComponent<TerrainLevels>();revision.demo=demo;revision.sun=sun;revision.clay=clay;revision.regolith=mat;
            revision.info=metadata.scenes[sceneIndex];revision.witnesses=metadata.scenes[sceneIndex].witnessIndices;demo.witnessIndices=revision.witnesses;revision.SetWitness(0);revision.SetLighting(false);Physics.SyncTransforms();
            revision.gameObject.AddComponent<TerrainLevelsPlayerSmoke>();
            string scene="Assets/LevelScenes/occlusion_levels_"+c.id+".unity";EditorSceneManager.SaveScene(SceneManager.GetActiveScene(),scene);scenePaths.Add(scene);AssetDatabase.SaveAssets();
            Debug.Log("REVISION_SCENE_BUILT "+c.id);
            }
            EditorBuildSettings.scenes=scenePaths.ConvertAll(s=>new EditorBuildSettingsScene(s,true)).ToArray();EditorSceneManager.OpenScene(scenePaths[0]);AssetDatabase.SaveAssets();
            File.WriteAllText(Path.Combine(Project,"Outputs","revision_build.json"),"{\"status\":\"SCENE_BUILD_PASS\",\"sceneCount\":"+all.scenes.Length+",\"terrainSurfaceCountPerScene\":1}");
            Debug.Log("REVISION_SCENE_BUILD_PASS");if(Application.isBatchMode&&!pipeline)EditorApplication.Exit(0);
        }catch(Exception ex){Debug.LogException(ex);if(Application.isBatchMode)EditorApplication.Exit(1);else throw;}
    }
    public static void BuildAndAudit(){pipeline=true;Build();TerrainLevelsSuite.Run();}
    [Serializable]class RevisionScene{public int[] witnessIndices;public float[] sourceOrigin;}
    [Serializable]class RevisionConfig{public RevisionScene[] scenes;}
    public static void BuildPlayer(){
        string path=Path.Combine(Directory.GetParent(Project).FullName,"WindowsDemo","LunarTerrainThreeLevels.exe");Directory.CreateDirectory(Path.GetDirectoryName(path));
        var report=BuildPipeline.BuildPlayer(EditorBuildSettings.scenes,path,BuildTarget.StandaloneWindows64,BuildOptions.None);
        File.WriteAllText(Path.Combine(Project,"Outputs","player_build.json"),"{\"result\":\""+report.summary.result+"\",\"errors\":"+report.summary.totalErrors+"}");EditorApplication.Exit(report.summary.totalErrors==0?0:1);
    }
}
