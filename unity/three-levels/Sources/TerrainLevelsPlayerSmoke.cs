using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using UnityEngine;
using UnityEngine.SceneManagement;

public class TerrainLevelsPlayerSmoke:MonoBehaviour {
    static bool active;
    void Start(){
        string[] args=Environment.GetCommandLineArgs();int index=Array.IndexOf(args,"--levels-smoke");
        if(index<0||index+1>=args.Length||active)return;active=true;
        var g=new GameObject("Revision runtime verification");DontDestroyOnLoad(g);g.AddComponent<TerrainLevelsSmokeRunner>().output=args[index+1];
    }
}
public class TerrainLevelsSmokeRunner:MonoBehaviour {
    public string output;
    [Serializable]public class Sample {public string role;public int redPixels,segmentationPixels,blockedRays;}
    [Serializable]public class SceneCheck {public string id,status;public bool playbackAdvanced,materialSwitch,levelNavigationAvailable,familyNavigationAvailable,navigationLoadedCorrectScene,comparisonViewPreserved;public List<Sample> witnesses=new List<Sample>();}
    [Serializable]public class Report {public string status,unityVersion,gpu;public bool robotWalkingTested=false,MuJoCoTested=false;public string scope="Windows player runtime, camera rendering and scripted control methods. Native mouse/keyboard interaction and robot walking are not tested.";public List<SceneCheck> scenes=new List<SceneCheck>();}
    IEnumerator Start(){
        Directory.CreateDirectory(output);yield return null;yield return null;
        var report=new Report{status="RUNNING",unityVersion=Application.unityVersion,gpu=SystemInfo.graphicsDeviceName};
        string[] ids={"barrier_a0","barrier_a1","barrier_a2","trench_a0","trench_a1","trench_a2","stairs_up_a0","stairs_up_a1","stairs_up_a2","pit_a0","pit_a1","pit_a2","basin_a0","basin_a1","basin_a2","waves_a0","waves_a1","waves_a2","perlin_a0","perlin_a1","perlin_a2","perlin_rough_a0","perlin_rough_a1","perlin_rough_a2"};
        foreach(string id in ids){
            var beforeNavigation=FindObjectOfType<TerrainLevels>();bool compare=false;Vector3 oldPosition=Vector3.zero;Quaternion oldRotation=Quaternion.identity;
            int split=id.LastIndexOf("_a",StringComparison.Ordinal);string familyId=id.Substring(0,split);int levelId=int.Parse(id.Substring(split+2));
            if(beforeNavigation!=null){beforeNavigation.SetOverview();compare=beforeNavigation.info.family==familyId;oldPosition=beforeNavigation.demo.viewCamera.transform.position;oldRotation=beforeNavigation.demo.viewCamera.transform.rotation;beforeNavigation.NavigateTo(familyId,levelId);}
            else SceneManager.LoadScene("occlusion_levels_"+id);
            yield return null;yield return null;yield return new WaitForSecondsRealtime(.1f);
            var r=FindObjectOfType<TerrainLevels>();var check=new SceneCheck{id=id,status="PASS",navigationLoadedCorrectScene=r.info.id==id,comparisonViewPreserved=!compare||(Vector3.Distance(oldPosition,r.demo.viewCamera.transform.position)<.001f&&Quaternion.Angle(oldRotation,r.demo.viewCamera.transform.rotation)<.01f)};
            if(!check.navigationLoadedCorrectScene||!check.comparisonViewPreserved)check.status="FAILED";
            string[] roles={"visible","hidden","recovered"};
            for(int k=0;k<3;k++){
                r.SetWitness(k);yield return null;Physics.SyncTransforms();
                var sample=new Sample{role=roles[k],blockedRays=r.demo.BlockedRays()};sample.redPixels=Render(r.demo.viewCamera,false,Path.Combine(output,id+"_"+roles[k]+".png"));sample.segmentationPixels=Render(r.demo.viewCamera,true,null);check.witnesses.Add(sample);
                bool correct=k==1?sample.redPixels==0&&sample.segmentationPixels==0&&sample.blockedRays==9:sample.redPixels>=40&&sample.segmentationPixels>=40&&sample.blockedRays<9;if(!correct)check.status="FAILED";
            }
            r.SetWitness(0);float before=r.demo.progress;r.playing=true;yield return new WaitForSecondsRealtime(.25f);check.playbackAdvanced=r.demo.progress>before;r.playing=false;
            r.SetMaterial(true);check.materialSwitch=r.demo.ground.sharedMaterial==r.clay;r.SetMaterial(false);check.materialSwitch&=r.demo.ground.sharedMaterial==r.regolith;
            if(!check.playbackAdvanced||!check.materialSwitch)check.status="FAILED";
            check.levelNavigationAvailable=true;check.familyNavigationAvailable=true;
            for(int level=0;level<3;level++){string scene=r.SceneFor(r.info.family,level);check.levelNavigationAvailable&=scene!=null&&Application.CanStreamedLevelBeLoaded(scene);}
            foreach(string family in TerrainLevels.Families){string scene=r.SceneFor(family,r.info.level);check.familyNavigationAvailable&=scene!=null&&Application.CanStreamedLevelBeLoaded(scene);}
            if(!check.levelNavigationAvailable||!check.familyNavigationAvailable)check.status="FAILED";
            r.SetOverview();yield return new WaitForEndOfFrame();ScreenCapture.CaptureScreenshot(Path.Combine(output,id+"_interface.png"));yield return null;yield return null;
            report.scenes.Add(check);File.WriteAllText(Path.Combine(output,"player_verification.json"),JsonUtility.ToJson(report,true));
        }
        bool pass=report.scenes.TrueForAll(s=>s.status=="PASS");report.status=pass?"WINDOWS_TWENTY_FOUR_LEVEL_SCENES_PASS":"FAILED";File.WriteAllText(Path.Combine(output,"player_verification.json"),JsonUtility.ToJson(report,true));Debug.Log(report.status);Application.Quit(pass?0:1);
    }
    static int Render(Camera cam,bool mask,string path){
        var rt=new RenderTexture(1920,1080,24,RenderTextureFormat.ARGB32,RenderTextureReadWrite.sRGB){antiAliasing=mask?1:4};var tex=new Texture2D(1920,1080,TextureFormat.RGB24,false);var previous=cam.targetTexture;var active=RenderTexture.active;var tone=cam.GetComponent<LunarToneEffect>();bool enabled=tone.enabled,msaa=cam.allowMSAA;
        try{rt.Create();cam.targetTexture=rt;if(mask){tone.enabled=false;cam.allowMSAA=false;cam.RenderWithShader(Shader.Find("OcclusionDemo/Segmentation"),"");}else cam.Render();RenderTexture.active=rt;tex.ReadPixels(new Rect(0,0,1920,1080),0,0);tex.Apply();if(path!=null)File.WriteAllBytes(path,tex.EncodeToPNG());int count=0;foreach(var p in tex.GetPixels32()){if(mask?p.r>127&&p.g>127&&p.b>127:p.r>100&&p.r>p.g*1.8f&&p.r>p.b*1.8f&&p.g<100)count++;}return count;}
        finally{tone.enabled=enabled;cam.allowMSAA=msaa;cam.targetTexture=previous;RenderTexture.active=active;rt.Release();Destroy(rt);Destroy(tex);}
    }
}
