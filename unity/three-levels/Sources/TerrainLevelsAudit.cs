using System;
using System.IO;
using UnityEngine;
using UnityEditor;
public static class TerrainLevelsAudit {
    static string Output{get{return Path.Combine(Directory.GetParent(Application.dataPath).FullName,"Outputs","LevelVerification");}}
    [Serializable] public class Sample {
        public int index,redPixels,segmentationPixels,blockedRays;
        public bool targetInFov,cameraClear;
        public string state;
    }
    public static Sample Capture(OcclusionDemo d,int index,int w,int h,string name){
        var cam=d.viewCamera;var vp=cam.WorldToViewportPoint(d.target.position);var rgb=Render(cam,w,h,false,name==null?null:name+".png");var mask=Render(cam,w,h,true,name==null?null:name+"_mask.png");
        int red=0,seg=0;for(int i=0;i<rgb.Length;i++){Color32 p=rgb[i];if(p.r>100&&p.r>p.g*1.8f&&p.r>p.b*1.8f&&p.g<100)red++;if(mask[i].r>127&&mask[i].g>127&&mask[i].b>127)seg++;}
        int rays=d.BlockedRays();return new Sample{index=index,redPixels=red,segmentationPixels=seg,blockedRays=rays,targetInFov=vp.z>0&&vp.x>.05f&&vp.x<.95f&&vp.y>.05f&&vp.y<.95f,cameraClear=!Physics.CheckSphere(cam.transform.position,.1f,(1<<8)|(1<<9),QueryTriggerInteraction.Ignore),state=red==0&&seg==0&&rays==9?"H":red>=16&&seg>=16&&rays<9?"V":"P"};
    }
    public static Color32[] Render(Camera cam,int w,int h,bool mask,string name){
        var rt=new RenderTexture(w,h,24,RenderTextureFormat.ARGB32,RenderTextureReadWrite.sRGB){antiAliasing=mask?1:4};var tex=new Texture2D(w,h,TextureFormat.RGB24,false);var previous=cam.targetTexture;var active=RenderTexture.active;var tone=cam.GetComponent<LunarToneEffect>();bool enabled=tone.enabled,msaa=cam.allowMSAA;
        try{rt.Create();cam.targetTexture=rt;if(mask){tone.enabled=false;cam.allowMSAA=false;cam.RenderWithShader(Shader.Find("OcclusionDemo/Segmentation"),"");}else cam.Render();RenderTexture.active=rt;tex.ReadPixels(new Rect(0,0,w,h),0,0);tex.Apply();if(name!=null)File.WriteAllBytes(Path.Combine(Output,name),tex.EncodeToPNG());return tex.GetPixels32();}
        finally{tone.enabled=enabled;cam.allowMSAA=msaa;cam.targetTexture=previous;RenderTexture.active=active;rt.Release();UnityEngine.Object.DestroyImmediate(rt);UnityEngine.Object.DestroyImmediate(tex);}
    }
}
