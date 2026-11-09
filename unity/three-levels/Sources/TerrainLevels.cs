using System;
using UnityEngine;
using UnityEngine.SceneManagement;

public class TerrainLevels : MonoBehaviour {
    public OcclusionDemo demo;
    public Light sun;
    public Material clay,regolith;
    public int[] witnesses;
    public bool playing,overview,clayMode,manual;
    public float speed=1.25f;
    Font font;
    CharacterController controller;
    Vector2 look;
    float verticalSpeed;
    public LevelSceneInfo info;
    public LevelConfig menu;
    public bool lowSun;
    static bool pending, pendingOverview, pendingClay, pendingLow;
    static float pendingFraction;
    static string pendingFamily;
    static Vector3 pendingPosition;
    static Quaternion pendingRotation;
    public static readonly string[] Families={"barrier","trench","stairs_up","pit","basin","waves","perlin","perlin_rough"};
    public static readonly string[] FamilyNames={"巨石屏障","连续沟槽","上行阶地","局部凹坑","宽阔凹地","连续丘脊","平滑随机起伏","岩块与强起伏"};
    public int IndexFor(string family,int level){
        if(menu==null)menu=JsonUtility.FromJson<LevelConfig>(demo.configuration.text);
        return Array.FindIndex(menu.scenes,c=>c.family==family&&c.level==level);
    }
    public string SceneFor(string family,int level){int i=IndexFor(family,level);return i<0?null:"occlusion_levels_"+menu.scenes[i].id;}
    public void NavigateTo(string family,int level){
        string scene=SceneFor(family,level);if(scene==null)throw new InvalidOperationException("Missing family/level scene");
        pending=true;pendingOverview=overview;pendingClay=clayMode;pendingLow=lowSun;pendingFamily=info.family;
        pendingFraction=demo.progress/Mathf.Max(1,demo.Data.route.Length-1);pendingPosition=demo.viewCamera.transform.position;pendingRotation=demo.viewCamera.transform.rotation;
        SceneManager.LoadScene(scene);
    }

    void Start(){
        font=Font.CreateDynamicFontFromOSFont(new[]{"Microsoft YaHei","SimHei","Arial"},20);
        menu=JsonUtility.FromJson<LevelConfig>(demo.configuration.text);
        controller=demo.viewCamera.GetComponent<CharacterController>();controller.enabled=false;
        Physics.IgnoreLayerCollision(10,9,true);
        SetLighting(false);
        SetWitness(0);
        if(pending){
            bool same=pendingFamily==info.family;SetMaterial(pendingClay);SetLighting(pendingLow);
            if(pendingOverview){SetOverview();if(same)demo.viewCamera.transform.SetPositionAndRotation(pendingPosition,pendingRotation);}
            else if(same)demo.SetProgress(pendingFraction*(demo.Data.route.Length-1));
            else SetOverview();pending=false;
        }else SetOverview();
    }
    public void StopMotion(){playing=false;manual=false;controller=demo.viewCamera.GetComponent<CharacterController>();controller.enabled=false;demo.routeLine.enabled=false;overview=false;}
    public void SetWitness(int index){StopMotion();demo.SetProgress(witnesses[Mathf.Clamp(index,0,2)]);}
    public void SetOverview(bool whole=false){
        StopMotion();overview=true;
        Vector3 focus=OcclusionDemo.V(info.comparisonFocus);
        demo.viewCamera.transform.position=focus+(whole?new Vector3(86,78,-102):new Vector3(35,34,-48));
        demo.viewCamera.transform.LookAt(focus);demo.routeLine.enabled=true;
    }
    public void SetBankView(){
        StopMotion();overview=true;
        demo.viewCamera.transform.position=OcclusionDemo.V(info.comparisonBankPosition);
        demo.viewCamera.transform.LookAt(OcclusionDemo.V(info.comparisonBankFocus));
    }
    public void SetMaterial(bool gray){clayMode=gray;demo.ground.sharedMaterial=gray?clay:regolith;}
    public void SetLighting(bool low){
        lowSun=low;sun.transform.rotation=Quaternion.LookRotation(-new Vector3(-.62f,low?.30f:.58f,.48f),Vector3.up);
        sun.intensity=low?1.35f:1.3f;
        RenderSettings.ambientLight=Color.white*(low?.065f:.075f);
    }
    public void BeginManual(){
        StopMotion();manual=true;look=new Vector2(demo.viewCamera.transform.eulerAngles.y,demo.viewCamera.transform.eulerAngles.x);
        controller.enabled=true;
    }
    void Update(){
        if(Input.GetKeyDown(KeyCode.O))SetOverview();
        if(Input.GetKeyDown(KeyCode.R))SetWitness(0);
        if(Input.GetKeyDown(KeyCode.Alpha1))SetWitness(0);
        if(Input.GetKeyDown(KeyCode.Alpha2))SetWitness(1);
        if(Input.GetKeyDown(KeyCode.Alpha3))SetWitness(2);
        if(Input.GetKeyDown(KeyCode.Space)){if(overview||manual||demo.progress>=demo.Data.route.Length-1){StopMotion();demo.SetProgress(0);}playing=!playing;}
        if(Input.GetKeyDown(KeyCode.Escape)){if(manual)StopMotion();else Application.Quit();}
        if(playing){
            int i=Mathf.Min((int)demo.progress,demo.Data.route.Length-2);
            float length=Vector3.Distance(OcclusionDemo.V(demo.Data.route[i].position),OcclusionDemo.V(demo.Data.route[i+1].position));
            demo.SetProgress(demo.progress+Time.deltaTime*speed/Mathf.Max(length,.01f));
            if(demo.progress>=demo.Data.route.Length-1)playing=false;
        }
        if(manual){
            if(Input.GetMouseButton(1)){look.x+=Input.GetAxis("Mouse X")*2;look.y=Mathf.Clamp(look.y-Input.GetAxis("Mouse Y")*2,-75,75);demo.viewCamera.transform.rotation=Quaternion.Euler(look.y,look.x,0);}
            Vector3 f=demo.viewCamera.transform.forward;f.y=0;f.Normalize();Vector3 r=demo.viewCamera.transform.right;r.y=0;r.Normalize();
            Vector3 move=(f*Input.GetAxis("Vertical")+r*Input.GetAxis("Horizontal"))*2;
            verticalSpeed=controller.isGrounded?-.2f:Mathf.Max(verticalSpeed-1.62f*Time.deltaTime,-10);move.y=verticalSpeed;controller.Move(move*Time.deltaTime);
            Vector3 p=demo.viewCamera.transform.position;
            if(Mathf.Abs(p.x)>90||Mathf.Abs(p.z)>90)SetWitness(0);
        }
    }
    void OnGUI(){
        if(demo==null||info==null)return;
        float scale=Mathf.Min(Screen.width/1600f,Screen.height/900f);GUI.matrix=Matrix4x4.Scale(new Vector3(scale,scale,1));
        float w=Screen.width/scale,h=Screen.height/scale;if(font!=null)GUI.skin.font=font;
        GUI.skin.label.fontSize=18;GUI.skin.button.fontSize=17;
        GUI.backgroundColor=new Color(.15f,.19f,.23f,.94f);GUI.Box(new Rect(20,20,350,736),"");
        GUI.Label(new Rect(38,34,320,35),"月面地形 · 八类三级",new GUIStyle(GUI.skin.label){fontSize=25,fontStyle=FontStyle.Bold});
        GUI.Label(new Rect(38,78,315,30),info.familyName+" / "+info.levelName,new GUIStyle(GUI.skin.label){fontSize=20,fontStyle=FontStyle.Bold});
        string[] levels={"一级 基础","二级 增强","三级 复合"};
        for(int level=0;level<3;level++){
            GUI.backgroundColor=level==info.level?new Color(.4f,.77f,.66f):new Color(.72f,.76f,.78f);
            if(GUI.Button(new Rect(38+level*106,123,100,38),levels[level]))NavigateTo(info.family,level);
        }
        GUI.Label(new Rect(38,172,312,38),info.levelDescription,new GUIStyle(GUI.skin.label){fontSize=15,wordWrap=true});
        for(int i=0;i<Families.Length;i++){
            GUI.backgroundColor=Families[i]==info.family?new Color(.45f,.72f,.67f):new Color(.75f,.77f,.78f);
            if(GUI.Button(new Rect(38,211+i*35,312,30),(i+1).ToString("00")+"  "+FamilyNames[i]))NavigateTo(Families[i],info.level);
        }
        GUI.backgroundColor=Color.white;
        GUI.Label(new Rect(38,500,312,61),demo.Data.description,new GUIStyle(GUI.skin.label){wordWrap=true,fontSize=16});
        if(GUI.Button(new Rect(38,575,145,36),"地形总览"))SetOverview();
        if(GUI.Button(new Rect(195,575,155,36),"近处观察"))SetBankView();
        if(GUI.Button(new Rect(38,622,145,36),playing?"暂停路线":"播放路线")){if(overview||manual){StopMotion();demo.SetProgress(0);}playing=!playing;}
        if(GUI.Button(new Rect(195,622,155,36),"自由观察"))BeginManual();
        if(GUI.Button(new Rect(38,669,145,36),clayMode?"月壤材质":"素色看形"))SetMaterial(!clayMode);
        if(GUI.Button(new Rect(195,669,155,36),"切换光照"))SetLighting(!lowSun);
        GUI.Label(new Rect(38,721,310,28),"O 总览 · 空格播放 · 1/2/3 关键位置",new GUIStyle(GUI.skin.label){fontSize=15});
        GUI.Box(new Rect(w-305,20,285,83),"");int blocked=demo.BlockedRays();
        string status=overview?"观察地形":manual?"自由观察":blocked==9?"目标被遮挡":blocked==0?"目标可见":"目标部分可见";
        GUI.Label(new Rect(w-287,31,255,32),status,new GUIStyle(GUI.skin.label){fontSize=24,fontStyle=FontStyle.Bold});
        GUI.Label(new Rect(w-287,69,255,26),"固定红球 · 路线视高 0.65 米",new GUIStyle(GUI.skin.label){fontSize=16});
        GUI.Box(new Rect(390,h-124,w-410,103),"");string[] labels={"① 看见目标","② 地形遮挡","③ 重新看见"};
        for(int i=0;i<3;i++)if(GUI.Button(new Rect(408+i*180,h-108,165,34),labels[i]))SetWitness(i);
        float changed=GUI.HorizontalSlider(new Rect(408,h-54,w-640,22),demo.progress,0,demo.Data.route.Length-1);
        if(Mathf.Abs(changed-demo.progress)>.01f){StopMotion();demo.SetProgress(changed);}
        GUI.Label(new Rect(w-205,h-63,170,27),(100*demo.progress/(demo.Data.route.Length-1)).ToString("F0")+"% · "+speed.ToString("F2")+" 米/秒");
        GUI.Label(new Rect(25,h-109,345,90),manual?"WASD 沿地面移动\n按住右键转动视线 · Esc 退出自由观察":"基础 / 增强 / 复合为设计档位。\n蓝线为预设相机路线。\n机器人行走尚未验证。",new GUIStyle(GUI.skin.label){fontSize=15,wordWrap=true});
        GUI.matrix=Matrix4x4.identity;
    }
    void OnDestroy(){if(font!=null)Destroy(font);}
}

[Serializable] public class LevelSceneInfo {
    public string id,family,familyName,levelName,levelDescription;
    public int level;
    public int[] witnessIndices;
    public float[] sourceOrigin,comparisonFocus,comparisonBankPosition,comparisonBankFocus;
}
[Serializable] public class LevelConfig {public string version;public LevelSceneInfo[] scenes;}
