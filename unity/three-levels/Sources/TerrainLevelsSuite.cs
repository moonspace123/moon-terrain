using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using System.Security.Cryptography;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEditor;
using UnityEditor.SceneManagement;

[InitializeOnLoad]
public static class TerrainLevelsSuite {
    const string Key="TerrainLevelsSuite.";
    [Serializable]public class SceneReport {
        public string id,status;
        public bool sourceHashUnchanged,allSamplesInFov,allSampleCamerasClear,playbackAdvanced,materialSwitch;
        public int terrainSurfaceCount,routePoints;
        public int[] witnessIndices;
        public List<TerrainLevelsAudit.Sample> samples=new List<TerrainLevelsAudit.Sample>();
        public List<TerrainLevelsAudit.Sample> witnesses=new List<TerrainLevelsAudit.Sample>();
        public List<string> errors=new List<string>();
    }
    [Serializable]public class Report {
        public string status,unityVersion,gpu,startedUtc,finishedUtc;
        public bool actualPlayMode,robotWalkingTested=false,MuJoCoTested=false;
        public List<SceneReport> scenes=new List<SceneReport>();
        public List<string> errors=new List<string>();
        public string scope="Twenty-four presentation scenes, eight families by three controlled design levels. GPU RGB, target-only segmentation, nine geometry rays, camera FOV/clearance, material switching and scripted route playback. No robot locomotion, dynamics or formal TASK3 benchmark is claimed.";
    }
    static string Project{get{return Directory.GetParent(Application.dataPath).FullName;}}
    static string Output{get{return Path.Combine(Project,"Outputs","LevelVerification");}}
    static string ReportPath{get{return Path.Combine(Output,"twenty_four_scene_verification.json");}}
    static readonly string[] Ids={"barrier_a0","barrier_a1","barrier_a2","trench_a0","trench_a1","trench_a2","stairs_up_a0","stairs_up_a1","stairs_up_a2","pit_a0","pit_a1","pit_a2","basin_a0","basin_a1","basin_a2","waves_a0","waves_a1","waves_a2","perlin_a0","perlin_a1","perlin_a2","perlin_rough_a0","perlin_rough_a1","perlin_rough_a2"};
    static Report report;
    static Vector3 overviewPosition;static Quaternion overviewRotation;
    static bool finishing;
    static TerrainLevelsSuite(){if(SessionState.GetBool(Key+"active",false)){EditorApplication.update-=Tick;EditorApplication.update+=Tick;Application.logMessageReceived+=Log;}}
    public static void Run(){
        EditorSceneManager.OpenScene("Assets/LevelScenes/occlusion_levels_barrier_a0.unity");Directory.CreateDirectory(Output);
        report=new Report{status="ENTERING_PLAY_MODE",unityVersion=Application.unityVersion,gpu=SystemInfo.graphicsDeviceName,startedUtc=DateTime.UtcNow.ToString("o")};Save();
        SessionState.SetBool(Key+"active",true);SessionState.SetInt(Key+"index",0);SessionState.SetString(Key+"phase","enter");EditorApplication.update-=Tick;EditorApplication.update+=Tick;Application.logMessageReceived+=Log;EditorApplication.isPlaying=true;
    }
    static void Settle(string phase){SessionState.SetFloat(Key+"settle",(float)EditorApplication.timeSinceStartup+.3f);SessionState.SetInt(Key+"frame",Time.frameCount);SessionState.SetString(Key+"phase",phase);}
    static bool Settled(){EditorApplication.QueuePlayerLoopUpdate();return EditorApplication.timeSinceStartup>SessionState.GetFloat(Key+"settle",0)&&Time.frameCount>SessionState.GetInt(Key+"frame",0)+1;}
    static void Tick(){
        if(finishing||!SessionState.GetBool(Key+"active",false))return;
        try{
            if(report==null)report=JsonUtility.FromJson<Report>(File.ReadAllText(ReportPath));
            string phase=SessionState.GetString(Key+"phase","");int index=SessionState.GetInt(Key+"index",0);
            if(phase=="enter"){if(!EditorApplication.isPlaying)return;report.actualPlayMode=true;SessionState.SetString(Key+"phase","load");Save();return;}
            if(phase=="load"){SceneManager.LoadScene("occlusion_levels_"+Ids[index]);Settle("audit");return;}
            if(phase=="audit"){
                if(!Settled())return;
                var result=Audit();report.scenes.Add(result);Save();var r=UnityEngine.Object.FindObjectOfType<TerrainLevels>();
                r.SetWitness(0);r.playing=true;SessionState.SetFloat(Key+"progress",r.demo.progress);Settle("playback");return;
            }
            if(phase=="playback"){
                if(!Settled())return;
                var r=UnityEngine.Object.FindObjectOfType<TerrainLevels>();var result=report.scenes.Last();result.playbackAdvanced=r.demo.progress>SessionState.GetFloat(Key+"progress",0);if(!result.playbackAdvanced)result.errors.Add("Playback did not advance");r.playing=false;
                Settle("complete");Save();return;
            }
            if(phase=="complete"){
                if(!Settled())return;
                var result=report.scenes.Last();result.status=result.errors.Count==0?"PASS":"FAILED";Debug.Log("REVISION_SUITE_SCENE "+result.id+" "+result.status);Save();
                if(index+1==Ids.Length){Finish();return;}SessionState.SetInt(Key+"index",index+1);SessionState.SetString(Key+"phase","load");
            }
        }catch(Exception ex){if(report==null)report=new Report();report.errors.Add(ex.ToString());Finish();}
    }
    static SceneReport Audit(){
        var r=UnityEngine.Object.FindObjectOfType<TerrainLevels>();var d=r.demo;r.StopMotion();r.SetLighting(false);r.SetMaterial(false);Physics.SyncTransforms();
        var result=new SceneReport{id=d.Data.id,routePoints=d.Data.route.Length};
        using(var hash=SHA256.Create())result.sourceHashUnchanged=BitConverter.ToString(hash.ComputeHash(File.ReadAllBytes(Path.Combine(Project,d.Data.sourceNative)))).Replace("-","").ToLowerInvariant()==d.Data.sourceSha256;
        result.terrainSurfaceCount=UnityEngine.Object.FindObjectsOfType<MeshFilter>().Count(f=>f.gameObject.name.StartsWith("Single continuous terrain"));
        r.SetOverview();TerrainLevelsAudit.Render(d.viewCamera,1920,1080,false,d.Data.id+"_overview.png");
        r.SetMaterial(true);result.materialSwitch=d.ground.sharedMaterial==r.clay;TerrainLevelsAudit.Render(d.viewCamera,1920,1080,false,d.Data.id+"_clay.png");r.SetMaterial(false);
        r.SetBankView();TerrainLevelsAudit.Render(d.viewCamera,1920,1080,false,d.Data.id+"_bank.png");r.StopMotion();
        for(int i=0;i<d.Data.route.Length;i+=2){d.SetProgress(i);Physics.SyncTransforms();result.samples.Add(TerrainLevelsAudit.Capture(d,i,1280,720,null));}
        var groups=new List<List<TerrainLevelsAudit.Sample>>();foreach(var s in result.samples){if(groups.Count==0||groups.Last()[0].state!=s.state)groups.Add(new List<TerrainLevelsAudit.Sample>());groups.Last().Add(s);}
        var stable=groups.Where(g=>g.Count>=2&&g[0].state!="P").ToList();List<TerrainLevelsAudit.Sample> a=null,b=null,c=null;
        for(int i=0;i+2<stable.Count;i++)if(stable[i][0].state=="V"&&stable[i+1][0].state=="H"&&stable[i+2][0].state=="V"){a=stable[i];b=stable[i+1];c=stable[i+2];break;}
        if(a==null){result.errors.Add("No stable rendered VHV: "+string.Join("",groups.Select(g=>g[0].state)));}
        else{
            result.witnessIndices=new[]{a[a.Count/2].index,b[b.Count/2].index,c[c.Count/2].index};r.witnesses=result.witnessIndices;d.witnessIndices=result.witnessIndices;
            string[] roles={"visible","hidden","recovered"};for(int k=0;k<3;k++){
                r.SetWitness(k);Physics.SyncTransforms();var s=TerrainLevelsAudit.Capture(d,result.witnessIndices[k],1920,1080,d.Data.id+"_"+roles[k]);result.witnesses.Add(s);
                bool correct=k==1?s.redPixels==0&&s.segmentationPixels==0&&s.blockedRays==9:s.redPixels>=40&&s.segmentationPixels>=40&&s.blockedRays<9;
                if(!correct)result.errors.Add("High-resolution witness failed: "+JsonUtility.ToJson(s));
            }
        }
        result.allSamplesInFov=result.samples.All(s=>s.targetInFov);result.allSampleCamerasClear=result.samples.All(s=>s.cameraClear);
        if(!result.sourceHashUnchanged)result.errors.Add("Source hash mismatch");if(result.terrainSurfaceCount!=1)result.errors.Add("Terrain surface count is not one");
        if(!result.allSamplesInFov)result.errors.Add("Target leaves FOV");if(!result.allSampleCamerasClear)result.errors.Add("Camera intersects geometry");
        return result;
    }
    static void Log(string text,string stack,LogType type){if(finishing||report==null)return;if(type==LogType.Error||type==LogType.Exception||type==LogType.Assert){report.errors.Add(text+"\n"+stack);Save();}}
    static void Save(){Directory.CreateDirectory(Output);File.WriteAllText(ReportPath,JsonUtility.ToJson(report,true));}
    static void Finish(){finishing=true;SessionState.SetBool(Key+"active",false);EditorApplication.update-=Tick;Application.logMessageReceived-=Log;
        bool passed=report.actualPlayMode&&report.errors.Count==0&&report.scenes.Count==24&&report.scenes.All(s=>s.status=="PASS");report.status=passed?"UNITY_TWENTY_FOUR_LEVEL_SCENES_PASS":"FAILED";report.finishedUtc=DateTime.UtcNow.ToString("o");Save();Debug.Log(report.status);EditorApplication.Exit(passed?0:1);
    }
    public static void PersistAndBuild(){
        var report=JsonUtility.FromJson<Report>(File.ReadAllText(ReportPath));if(report.status!="UNITY_TWENTY_FOUR_LEVEL_SCENES_PASS")throw new Exception("Twenty-four-scene audit did not pass");
        // The segmentation shader is selected by name at runtime, so retain it
        // explicitly when Unity strips shaders that are not used by materials.
        var graphics=new SerializedObject(AssetDatabase.LoadAllAssetsAtPath("ProjectSettings/GraphicsSettings.asset")[0]);var shaders=graphics.FindProperty("m_AlwaysIncludedShaders");var segmentation=Shader.Find("OcclusionDemo/Segmentation");bool included=false;
        for(int i=0;i<shaders.arraySize;i++)included|=shaders.GetArrayElementAtIndex(i).objectReferenceValue==segmentation;
        if(!included){int index=shaders.arraySize;shaders.InsertArrayElementAtIndex(index);shaders.GetArrayElementAtIndex(index).objectReferenceValue=segmentation;graphics.ApplyModifiedPropertiesWithoutUndo();}
        foreach(var s in report.scenes){EditorSceneManager.OpenScene("Assets/LevelScenes/occlusion_levels_"+s.id+".unity");var r=UnityEngine.Object.FindObjectOfType<TerrainLevels>();r.witnesses=s.witnessIndices;r.demo.witnessIndices=s.witnessIndices;r.SetWitness(0);EditorSceneManager.SaveScene(SceneManager.GetActiveScene());}
        var paths=new List<EditorBuildSettingsScene>{new EditorBuildSettingsScene("Assets/LevelScenes/occlusion_levels_trench_a0.unity",true)};foreach(var id in Ids)if(id!="trench_a0")paths.Add(new EditorBuildSettingsScene("Assets/LevelScenes/occlusion_levels_"+id+".unity",true));EditorBuildSettings.scenes=paths.ToArray();
        EditorSceneManager.OpenScene("Assets/LevelScenes/occlusion_levels_trench_a0.unity");AssetDatabase.SaveAssets();TerrainLevelsBuilder.BuildPlayer();
    }
}
