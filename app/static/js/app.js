async function loadV5Overview(){const el=document.getElementById("v5Stats");if(!el)return;try{const x=await api("/api/v5/overview"),d=x.data,r=d.role;const a=r==="student"?[["Courses",d.courses||0,"📚"],["Lessons completed",d.lessons_completed||0,"✅"],["Assessments",d.assessments||0,"📝"],["Notifications",d.notifications||0,"🔔"]]:r==="parent"?[["Linked child",d.child?1:0,"👤"],["Notifications",d.notifications||0,"🔔"],["Progress","Live","📈"],["Volo AI","Ready","🤖"]]:[["Students",d.students||0,"👥"],["Courses",d.courses||0,"📚"],[r==="tutor"?"Assessments":"Practical labs",d.assignments||d.practicals||0,r==="tutor"?"📝":"🔬"],["Notifications",d.notifications||0,"🔔"]];el.innerHTML=a.map(i=>`<div class="stat v5-stat"><span>${i[2]} ${esc(i[0])}</span><b>${esc(i[1])}</b><small>Volo platform snapshot</small></div>`).join("")}catch(e){el.innerHTML=`<div class="stat"><span>Volo</span><b>Ready</b><small>${esc(e.message)}</small></div>`}}async function loadV5Profile(){const el=document.getElementById("profileCard");if(!el)return;try{const x=await api("/api/v5/profile"),d=x.data;el.innerHTML=`<div class="avatar">${esc((d.full_name||"V").slice(0,1).toUpperCase())}</div><div><b>${esc(d.full_name)}</b><span>${esc((d.role||"").replace("_"," "))} · ${esc(d.class_name||d.subject_focus||"Volo user")}</span><small>${esc(d.email||"Profile ready for expansion")}</small></div>`}catch(e){el.textContent="Profile unavailable"}}document.addEventListener("DOMContentLoaded",()=>{loadV5Overview();loadV5Profile()});
async function api(url,opts={}){const r=await fetch(url,opts);const j=await r.json();if(!j.ok)throw new Error(j.error||"Request failed");return j}
function esc(s){return String(s??"").replace(/[&<>"']/g,m=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[m]))}
function toast(m){alert(m)}
async function loadStats(){const el=document.getElementById("stats");if(!el)return;const x=await api("/api/stats");el.innerHTML=Object.entries({Students:x.students,Tutors:x.tutors,Courses:x.courses,Lessons:x.lessons}).map(([k,v])=>`<div class="stat"><span>${k}</span><b>${v}</b></div>`).join("")}
async function loadCourses(target="courses"){const el=document.getElementById(target);if(!el)return;const x=await api("/api/courses");el.innerHTML=x.data.map(c=>`<a class="card course" href="/course/${c.id}"><div class="banner" style="background:${esc(c.color)}">${esc(c.title)}</div><div class="coursebody"><h2>${esc(c.title)}</h2><p>${esc(c.description)}</p><small>${c.lesson_count} lessons</small></div></a>`).join("")}
async function loadStudents(){const el=document.getElementById("students");if(!el)return;const x=await api("/api/students");el.innerHTML=x.data.map(s=>`<tr><td>${esc(s.full_name)}</td><td>${esc(s.username)}</td><td>${esc(s.class_name||"—")}</td><td>${s.courses}</td></tr>`).join("")}
async function addStudent(){const name=prompt("Full name");if(!name)return;const username=prompt("Username");if(!username)return;const password=prompt("Temporary password");if(!password)return;const cls=prompt("Class","Form 2A");try{await api("/api/students",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({full_name:name,username,password,class_name:cls})});loadStudents()}catch(e){toast(e.message)}}
async function addCourse(){const title=prompt("Course title");if(!title)return;const description=prompt("Description","New module");try{await api("/api/courses",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({title,description})});loadCourses("manageCourses")}catch(e){toast(e.message)}}
async function askAI(){const q=document.getElementById("q");const m=document.getElementById("messages");if(!q||!q.value.trim())return;const text=q.value.trim();m.innerHTML+=`<div class="msg user">${esc(text)}</div>`;q.value="";m.innerHTML+=`<div class="msg bot">AI integration endpoint is ready. The next stage will connect this tutor to the selected AI provider, learner context and course materials.</div>`}
document.addEventListener("DOMContentLoaded",()=>{loadStats();loadCourses();loadCourses("manageCourses");loadStudents();const s=document.getElementById("salt");if(s){s.oninput=()=>document.getElementById("saltv").textContent=s.value+"%"}});

async function loadLessonPlanner(){
 const form=document.getElementById("lessonPlanner");if(!form)return;const course=document.getElementById("lessonCourse"),indicator=document.getElementById("lessonIndicators"),status=document.getElementById("lessonPlannerStatus");
 try{const [courses,curriculum]=await Promise.all([api("/api/courses"),api("/api/curriculum")]);course.innerHTML='<option value="">Select a course</option>'+courses.data.map(c=>`<option value="${c.id}">${esc(c.code||"")} · ${esc(c.title)}</option>`).join("");indicator.innerHTML=curriculum.data.map(r=>`<option value="${r.indicator_id}">${esc(r.indicator_code)} — ${esc(r.indicator_description)}</option>`).join("");form.onsubmit=async e=>{e.preventDefault();if(!course.value){status.textContent="Select a course.";return}const data=new FormData(form);try{const result=await api(`/api/courses/${course.value}/lessons`,{method:"POST",body:data});status.textContent=`Lesson #${result.id} created with curriculum mapping.`;form.reset();await loadCourses("manageCourses")}catch(err){status.textContent=err.message}}}catch(e){status.textContent=`Planner unavailable: ${e.message}`}
}
document.addEventListener("DOMContentLoaded",loadLessonPlanner);

async function loadCourseDetail(){
 const lessons=document.getElementById("lessons"); if(!lessons)return;
 const id=location.pathname.split("/").pop(); const x=await api("/api/courses/"+id);
 document.getElementById("ctitle").textContent=x.course.title;
 document.getElementById("cdesc").textContent=x.course.description||"";
 const done=x.lessons.filter(l=>l.completed).length, total=x.lessons.length, pct=total?Math.round(done/total*100):0;
 document.getElementById("pct").textContent=pct+"%"; document.getElementById("barfill").style.width=pct+"%";
 lessons.innerHTML=x.lessons.map(l=>`<div class="lesson"><div>${l.has_preparation?`<a class="lesson-link" href="/lesson/${l.id}">${esc(l.title)}</a>`:`<b>${esc(l.title)}</b>`}<small>${esc(l.material_type)}${l.has_preparation?" · Prepared learning module":""}</small></div>${l.completed?'<span class="done">Completed</span>':sessionRole==="student"?`<button onclick="completeLesson(${l.id})">Mark complete</button>`:""}</div>`).join("");
 const qb=document.getElementById("quizbox");
 if(x.quiz) qb.innerHTML=`<div class="assessment-item"><b>Quiz</b><span>${esc(x.quiz.title)}</span><a class="buttonlink" href="/course/${id}/quiz/${x.quiz.id}">Open quiz</a></div>`; else qb.innerHTML="<p class='muted'>No quiz published yet.</p>";
 const al=document.getElementById("assignmentList");
 al.innerHTML=(x.assignments||[]).length?`<h3>Assignments</h3>`+(x.assignments||[]).map(a=>`<div class="assessment-item"><b>${esc(a.title)}</b><span>${esc(a.max_points)} points${a.due_at?` · Due ${esc(a.due_at)}`:""}</span>${sessionRole==="student"?(a.submission_status?`<span class="done">${esc(a.submission_status)}${a.submission_score!=null?` · ${esc(a.submission_score)}/${esc(a.max_points)}`:""}</span>`:`<a class="buttonlink secondary" href="/course/${id}/assignment/${a.id}">Open & submit</a>`):`<span class="muted">Created by ${esc(a.creator||"Teacher")}</span>`}</div>`).join(""):"<p class='muted'>No assignments published yet.</p>";
 const create=document.getElementById("assignmentCreate");
 if(create && ["tutor","admin","super_admin"].includes(sessionRole)){create.hidden=false;document.getElementById("assignmentForm").onsubmit=async e=>{e.preventDefault();const raw=Object.fromEntries(new FormData(e.target));try{await api(`/api/courses/${id}/assignments`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(raw)});document.getElementById("assignmentStatus").textContent="Assignment published.";e.target.reset();loadCourseDetail()}catch(err){document.getElementById("assignmentStatus").textContent=err.message}}}
}
async function completeLesson(id){await api("/api/progress/"+id+"/complete",{method:"POST"});loadCourseDetail()}
const sessionRole = document.body.dataset.role || "";
document.addEventListener("DOMContentLoaded",loadCourseDetail)

async function loadLessonPreparation(){
 const view=document.getElementById("lessonView");if(!view)return;const id=location.pathname.split("/").pop();
 try{const x=await api("/api/lessons/"+id+"/preparation"),p=x.data;const outcomes=p.learning_outcomes.map(v=>`<li>${esc(v)}</li>`).join(""),vocabulary=p.vocabulary.map(v=>`<span>${esc(v)}</span>`).join("");const labs=p.lab_ids.length?`<section class="panel lesson-labs"><div class="panel-heading"><h2>Linked virtual practicals</h2><span>Perform, record, analyse</span></div><div>${p.lab_ids.map(id=>`<a class="buttonlink secondary" href="/practical-studio#${encodeURIComponent(id)}">Open practical laboratory</a>`).join(" ")}</div></section>`:"";view.innerHTML=`<header class="v5-head lesson-page-head"><div><div class="eyebrow">${esc(p.source_section)}</div><h1>${esc(p.title)}</h1><p>${esc(p.course_title)} · Source: ${esc(p.source_file)}, p. ${esc(p.source_page)}</p></div><a class="buttonlink secondary" href="/courses">Back to learning</a></header><section class="lesson-overview panel"><div><span class="source-badge">${esc(p.alignment_status)}</span><h2>Learning outcomes</h2><ul>${outcomes}</ul><div class="lesson-meta"><div><b>Prior knowledge</b><p>${esc(p.prior_knowledge)}</p></div><div><b>Key vocabulary</b><p class="vocabulary">${vocabulary}</p></div></div></section><section class="lesson-journey"><article class="panel lesson-stage"><span>1</span><div><h2>Engage</h2><p>${esc(p.engage)}</p></div></article><article class="panel lesson-stage"><span>2</span><div><h2>Investigate</h2><p>${esc(p.investigate)}</p></div></article><article class="panel lesson-stage"><span>3</span><div><h2>Explain</h2><p>${esc(p.explain)}</p></div></article><article class="panel lesson-stage"><span>4</span><div><h2>Apply and elaborate</h2><p>${esc(p.elaborate)}</p></div></article></section><section class="lesson-practical panel"><div class="panel-heading"><h2>Practical work</h2><span>Plan · observe · analyse · conclude</span></div><p>${esc(p.practical_work)}</p><div class="safety-box"><b>Safety and inclusion</b><p>${esc(p.safety_notes)}</p></div></section>${labs}<section class="lesson-assess-grid"><article class="panel"><h2>Check for understanding</h2><p>${esc(p.assessment)}</p></article><article class="panel"><h2>Extension / enrichment</h2><p>${esc(p.extension)}</p></article></section>`}catch(e){view.innerHTML=`<div class="panel lesson-loading">${esc(e.message)}</div>`}
}
document.addEventListener("DOMContentLoaded",loadLessonPreparation)

async function loadQuiz(){
 const qbox=document.getElementById("questions");if(!qbox)return;
 const parts=location.pathname.split("/"), quizId=parts[parts.length-1], x=await api("/api/quizzes/"+quizId);
 document.getElementById("qtitle").textContent=x.quiz.title;
 document.getElementById("qmeta").textContent=(x.quiz.time_limit_minutes?x.quiz.time_limit_minutes+" minutes · ":"")+x.questions.length+" questions";
 qbox.innerHTML=x.questions.map((q,i)=>`<div class="question"><b>${i+1}. ${esc(q.question_text)}</b>
 <label><input type="radio" name="q${q.id}" value="1"> ${esc(q.option_a)}</label>
 <label><input type="radio" name="q${q.id}" value="2"> ${esc(q.option_b)}</label>
 <label><input type="radio" name="q${q.id}" value="3"> ${esc(q.option_c)}</label>
 <label><input type="radio" name="q${q.id}" value="4"> ${esc(q.option_d)}</label></div>`).join("");
 document.getElementById("quizform").onsubmit=async e=>{e.preventDefault();const answers={};x.questions.forEach(q=>{const r=document.querySelector(`input[name="q${q.id}"]:checked`);answers[q.id]=r?r.value:null});try{const r=await api("/api/quizzes/"+quizId+"/submit",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({answers})});document.getElementById("result").innerHTML=`<div class="result"><h2>Result: ${r.score}/${r.total}</h2><p>${r.percentage}%</p><a class="buttonlink" href="/course/${parts[parts.indexOf("course")+1]}">Back to course</a></div>`;document.getElementById("quizform").style.display="none"}catch(err){alert(err.message)}};
}
document.addEventListener("DOMContentLoaded",loadQuiz)

async function loadCurriculum(){
 const results=document.getElementById("curriculumResults");if(!results)return;
 const year=document.getElementById("curriculumYear"),strand=document.getElementById("curriculumStrand"),search=document.getElementById("curriculumSearch"),summary=document.getElementById("curriculumSummary");
 try{
  const facets=await api("/api/curriculum/facets");
  year.innerHTML+=""+facets.years.map(x=>`<option value="${esc(x.code)}">${esc(x.title)}</option>`).join("");
  strand.innerHTML+=""+facets.strands.map(x=>`<option value="${esc(x.code)}">${esc(x.code)} · ${esc(x.title)}</option>`).join("");
  const c=facets.counts;summary.innerHTML=[["Content standards",c.standards],["Learning outcomes",c.outcomes],["Learning indicators",c.indicators]].map(x=>`<div class="stat"><span>${esc(x[0])}</span><b>${esc(x[1])}</b><small>Verified records</small></div>`).join("");
  const render=async()=>{const p=new URLSearchParams();if(year.value)p.set("year",year.value);if(strand.value)p.set("strand",strand.value);if(search.value.trim())p.set("q",search.value.trim());const rows=await api("/api/curriculum?"+p);results.innerHTML=rows.data.length?rows.data.map(r=>`<article class="curriculum-record"><header><span class="curriculum-path">${esc(r.year_code)} · Strand ${esc(r.strand_code)} · ${esc(r.substrand_title)}</span><span class="source-page">PDF p. ${esc(r.source_page)}</span></header><div class="curriculum-level"><code>${esc(r.standard_code)}</code><p>${esc(r.standard_description)}</p></div><div class="curriculum-level"><code>${esc(r.outcome_code||"—")}</code><p>${esc(r.outcome_description||"No linked learning outcome recorded.")}</p></div><div class="curriculum-indicator"><code>${esc(r.indicator_code)}</code><b>${esc(r.indicator_description)}</b><span>Assessment: ${esc(r.assessment_code||"—")} · Linked lessons: ${esc(r.lesson_count)}</span></div></article>`).join(""):'<div class="empty-curriculum">No verified curriculum records match these filters.</div>'};
  let timer;search.oninput=()=>{clearTimeout(timer);timer=setTimeout(render,180)};year.onchange=render;strand.onchange=render;await render();
 }catch(e){results.innerHTML=`<div class="empty-curriculum">Curriculum data is unavailable: ${esc(e.message)}</div>`}
}
document.addEventListener("DOMContentLoaded",loadCurriculum)


/* ============================================================
   V4 REALISTIC VIRTUAL LABORATORIES
   Source basis: uploaded General Science Year 1 Sections 1–9.
   ============================================================ */

const LABS = {
  "s1-p6": {section:"Section 1",title:"Investigating the presence of starch in plants",type:"Experiment",
    safety:"Handle iodine carefully and follow teacher/laboratory instructions.",
    apparatus:["Leaf sample","Potato sample","Iodine solution","Dropper","White tile","Forceps"],
    steps:[
      ["Prepare samples","Place the selected plant material on the white tile.","sample"],
      ["Apply iodine","Use the dropper to place iodine solution on the sample.","iodine"],
      ["Observe","Compare the colour change and record the observation.","observe"],
      ["Conclude","State whether starch is present and support your answer with the observation.","conclude"]
    ],engine:"starch"},
  "s1-p11": {section:"Section 1",title:"Produce a solar oven",type:"Design Practical",
    safety:"Use scissors/box knife only under appropriate supervision. Do not stare at concentrated sunlight.",
    apparatus:["Cardboard box","Aluminium foil","Clear tape","Plastic wrap","Black paper","Thermometer","Chocolate/marshmallow"],
    steps:[["Prepare box","Create the reflector flap and line the relevant surfaces.","build"],["Reflect sunlight","Adjust the foil reflector toward the light source.","angle"],["Insulate","Close the oven and minimise heat loss.","insulate"],["Measure","Place the thermometer and record temperature over time.","measure"],["Evaluate","Suggest a design improvement based on the evidence.","conclude"]],engine:"solar_oven"},
  "s1-p12": {section:"Section 1",title:"Balloon-powered cars",type:"Design Practical",
    safety:"Use scissors carefully. Keep the test track clear.",
    apparatus:["Bottle body","Straws","Balloon","Bottle caps","Axles","Tape","Cardboard body"],
    steps:[["Build chassis","Assemble the body, axles and wheels.","build"],["Attach balloon","Connect the balloon so escaping air can propel the car.","balloon"],["Test","Release the car on the track.","run"],["Measure","Record travel distance and time.","measure"],["Improve","Change one design variable and retest.","improve"]],engine:"balloon_car"},
  "s1-p5": {section:"Section 1",title:"The Simple Pendulum Experiment",type:"Experiment",
    safety:"Secure the stand and keep the swing path clear.",
    apparatus:["Retort stand","String","Bob","Ruler","Stopwatch"],
    steps:[["Set length","Set the pendulum to a measured length.","setup"],["Release","Displace the bob slightly and release without pushing.","release"],["Time swings","Time a fixed number of complete oscillations.","time"],["Repeat","Repeat using the same conditions to test consistency.","repeat"],["Analyse","Calculate period and compare trials.","analyse"]],engine:"pendulum"},
  "s2-p5": {section:"Section 2",title:"Comparing the lustre of different metals",type:"Experiment",
    safety:"Handle metal samples carefully and avoid sharp edges.",
    apparatus:["Iron","Copper","Aluminium","Gold","Silver","Sandpaper","Flashlight","Dark surface"],
    steps:[["Inspect","Observe each sample before cleaning.","inspect"],["Clean","Rub the surface with sandpaper as directed.","clean"],["Illuminate","Position the light so reflected light can be observed.","light"],["Compare","Rank the samples by apparent lustre.","compare"],["Conclude","Explain differences using your observations.","conclude"]],engine:"lustre"},
  "s2-p6": {section:"Section 2",title:"Demonstrating hardness of metals",type:"Experiment",
    safety:"Apply controlled force and keep samples stable.",
    apparatus:["Metal spoon","Key","Rubber band","Plastic ruler","Wood","Coin"],
    steps:[["Arrange","Place samples on a stable surface.","setup"],["Scratch","Use the coin with controlled pressure.","scratch"],["Observe","Record which surfaces are scratched.","observe"],["Compare","Compare metal and non-metal samples.","compare"],["Conclude","Rank relative hardness from your observations.","conclude"]],engine:"hardness"},
  "s2-p13": {section:"Section 2",title:"Electrical conductivity of solid materials",type:"Experiment",
    safety:"Use only the low-voltage educational circuit. Do not connect unknown objects to mains electricity.",
    apparatus:["Battery","LED bulb","Wires","Metal rod","Key","Wooden stick","Plastic ruler","Graphite rod"],
    steps:[["Build circuit","Connect the battery, wires and LED to create a test circuit.","build"],["Insert sample","Place one material into the circuit gap.","insert"],["Test","Complete the circuit and observe the LED.","test"],["Repeat","Test the remaining materials one at a time.","repeat"],["Classify","Classify the materials as conductors or poor/non-conductors.","classify"]],engine:"conductivity"},
  "s3-p2": {section:"Section 3",title:"Diffusion using potassium permanganate",type:"Experiment",
    safety:"Avoid direct contact with potassium permanganate and do not disturb the water unnecessarily.",
    apparatus:["Beaker","Water","Potassium permanganate crystal","Spatula","Timer"],
    steps:[["Fill beaker","Fill the beaker with water.","fill"],["Add crystal","Place the crystal carefully at the bottom.","add"],["Wait","Observe without stirring.","wait"],["Compare","Repeat with colder water if directed.","compare"],["Explain","Explain movement from high to low concentration.","conclude"]],engine:"diffusion"},
  "s3-p3": {section:"Section 3",title:"Diffusion of perfume through air",type:"Demonstration",
    safety:"Use a small amount of inexpensive perfume in a well-ventilated space.",
    apparatus:["Perfume","Tissue","Timer","Classroom map"],
    steps:[["Place perfume","Put a small amount on tissue in one corner.","place"],["Wait","Raise your hand when the scent is detected.","wait"],["Record","Record time and your position.","record"],["Compare","Compare distance and detection time among locations.","compare"],["Explain","Relate the observation to diffusion.","conclude"]],engine:"gas_diffusion"},
  "s3-p7": {section:"Section 3",title:"Osmosis in model cells using Visking tubing",type:"Experiment",
    safety:"Use clean apparatus and do not consume laboratory solutions.",
    apparatus:["Visking tubing","4 beakers","Water","5% sucrose","10% sucrose","15% sucrose","String","Funnel","Ruler"],
    steps:[["Prepare tubing","Cut equal lengths and tie one end.","cut"],["Fill cells","Fill with water or the specified sucrose solution.","fill"],["Measure","Measure starting circumference.","measure"],["Immerse","Place each model cell in water.","immerse"],["Wait 24 h","Allow the experiment to run for 24 hours.","wait"],["Measure again","Record final circumference and firmness.","final"],["Explain","Explain water movement across the selectively permeable membrane.","conclude"]],engine:"osmosis"},
  "s3-p8": {section:"Section 3",title:"Osmosis in plant tissues",type:"Experiment",
    safety:"Use a suitable knife/borer under supervision.",
    apparatus:["Potato","Borer/knife","0% sucrose","5% sucrose","10% sucrose","15% sucrose","Beakers","Ruler","Balance"],
    steps:[["Prepare cores","Cut equal-sized potato pieces.","cut"],["Measure","Record initial length/mass.","measure"],["Immerse","Place samples in the different solutions.","immerse"],["Wait","Leave for the specified period.","wait"],["Measure again","Record final dimensions/mass.","final"],["Explain","Use osmosis to explain changes.","conclude"]],engine:"potato_osmosis"},
  "s4-p4": {section:"Section 4",title:"Pollination simulation",type:"Simulation",
    safety:"Handle dissected flowers/models carefully.",
    apparatus:["Flower model","Pollen model","Bee/butterfly model","Wind fan","Paper","Camera"],
    steps:[["Select agent","Choose wind or insect pollination.","select"],["Transfer pollen","Move pollen from anther to stigma using the selected agent.","transfer"],["Observe","Identify the structures involved.","observe"],["Compare","Compare wind and insect adaptations.","compare"],["Present","Prepare a short explanation of the process.","conclude"]],engine:"pollination"},
  "s4-p8": {section:"Section 4",title:"Vegetative propagation through cuttings",type:"Simulation",
    safety:"Use clean cutting tools and appropriate plant material.",
    apparatus:["Healthy parent plant","Pruners","Rooting medium","Pot","Water spray","Labels"],
    steps:[["Select stem","Choose a healthy mature parent stem.","select"],["Cut","Make a clean cutting.","cut"],["Plant","Place the cutting in the rooting medium.","plant"],["Maintain","Provide suitable moisture and conditions.","maintain"],["Observe","Record evidence of rooting and growth.","observe"]],engine:"cuttings"},
  "s4-p9": {section:"Section 4",title:"Vegetative propagation through grafting",type:"Simulation",
    safety:"Use sharp tools only under supervision and keep cut surfaces clean.",
    apparatus:["Rootstock","Scion","Clean grafting knife","Grafting tape","Labels"],
    steps:[["Select","Choose compatible rootstock and scion.","select"],["Prepare","Make matching cuts.","cut"],["Join","Align the compatible tissues.","join"],["Secure","Wrap the graft securely.","secure"],["Observe","Monitor for successful union.","observe"]],engine:"grafting"},
  "s4-p10": {section:"Section 4",title:"Vegetative propagation through layering",type:"Simulation",
    safety:"Avoid damaging the parent plant unnecessarily.",
    apparatus:["Flexible stem","Pruners","Rooting medium","Pot","Stake","Twine","Water"],
    steps:[["Select branch","Choose a healthy flexible low-growing stem.","select"],["Prepare","Position the stem and expose the appropriate area.","prepare"],["Layer","Secure the stem into rooting medium.","layer"],["Maintain","Keep the medium suitably moist.","maintain"],["Observe","Record evidence of rooting.","observe"]],engine:"layering"},
  "s4-p11": {section:"Section 4",title:"Micropropagation / tissue culture",type:"Simulation",
    safety:"Sterility is essential. Use a suitable sterile workspace and sterilised tools.",
    apparatus:["Young plant tissue","Sterile workspace","Scalpel","Forceps","MS culture medium","Auxins","Cytokinins"],
    steps:[["Select tissue","Choose healthy young plant material.","select"],["Sterilise","Prepare tools/workspace according to the laboratory procedure.","sterilise"],["Place explant","Transfer tissue to culture medium.","place"],["Regulate growth","Use the specified plant growth regulators.","regulate"],["Observe","Monitor development under controlled conditions.","observe"]],engine:"micropropagation"},
  "s5-p8": {section:"Section 5",title:"Solar panel output under different lighting conditions",type:"Experiment",
    safety:"Use the educational solar kit and multimeter correctly; avoid short circuits.",
    apparatus:["Solar panel kit","Multimeter","Connecting wires","Small motor/light","Mounting stand","Light source"],
    steps:[["Connect","Connect the solar panel and measurement circuit.","connect"],["Direct sunlight","Measure voltage and current.","sun"],["Partial shade","Repeat under partial shade.","shade"],["Artificial light","Repeat under artificial light.","artificial"],["Calculate","Calculate power using P = V × I.","calculate"],["Analyse","Compare the outputs.","conclude"]],engine:"solar_panel"},
  "s5-p9": {section:"Section 5",title:"Environmental factors affecting solar panels",type:"Investigation",
    safety:"Handle hot water/ice packs and electrical equipment carefully.",
    apparatus:["Two small solar panels","Clear containers","Ice pack","Hot water bottle","Thermometer"],
    steps:[["Prepare","Set up identical panels/loads.","setup"],["Temperature test","Compare outputs under different temperatures.","temperature"],["Orientation test","Compare panel orientation/angle.","orientation"],["Environment","Consider wind, rain and dust effects.","environment"],["Conclude","Recommend installation conditions.","conclude"]],engine:"solar_environment"},
  "s6-p2": {section:"Section 6",title:"Effects of different surfaces and friction",type:"Experiment",
    safety:"Keep the track clear and avoid pushing objects toward people.",
    apparatus:["Wooden block/book/toy car","Smooth surface","Rough surface","Ruler/tape"],
    steps:[["Smooth trial","Push the object with a constant force and measure distance.","smooth"],["Record","Record the distance travelled.","record"],["Rough trial","Repeat on the rough surface with the same push.","rough"],["Compare","Compare both distances.","compare"],["Explain","Explain the role of friction.","conclude"]],engine:"friction"},
  "s6-p4": {section:"Section 6",title:"Investigating gravitational force",type:"Experiment",
    safety:"Drop objects only in a safe area and avoid heavy objects.",
    apparatus:["Spring scale","Light object","Heavy object","String","Ruler"],
    steps:[["Calibrate","Zero the spring scale.","zero"],["Measure","Measure the objects as instructed.","measure"],["Calculate","Use F = mg with mass in kilograms.","calculate"],["Drop test","Release objects from the same height if directed.","drop"],["Discuss","Compare the observations with expectations.","conclude"]],engine:"gravity"},
  "s6-p5": {section:"Section 6",title:"Exploring velocity",type:"Experiment",
    safety:"Keep the ramp stable and the track clear.",
    apparatus:["Stopwatch","Measuring tape","Toy car","Plank/ramp","Books"],
    steps:[["Mark 1 m","Measure a one-metre track.","mark"],["Set ramp","Raise one end using a stable support.","ramp"],["Release","Start timing as the car moves.","release"],["Calculate","Calculate velocity from displacement/time.","calculate"],["Repeat","Increase ramp height and repeat.","repeat"]],engine:"velocity"},
  "s6-p8": {section:"Section 6",title:"Cohesive and adhesive forces",type:"Experiment",
    safety:"Keep liquids away from electrical equipment.",
    apparatus:["Water","Salt","Two containers","Pipette","Paper towel","Small objects","Capillary tube/straw","Tissue"],
    steps:[["Prepare","Prepare plain water and saltwater.","prepare"],["Droplet test","Compare droplet behaviour on a clean surface.","drop"],["Capillary test","Observe water movement through a narrow tube/tissue.","capillary"],["Compare","Identify cohesion and adhesion evidence.","compare"],["Explain","Relate the observations to the forces.","conclude"]],engine:"cohesion"},
  "s7-p3": {section:"Section 7",title:"Build an LED circuit",type:"Electronics Practical",
    safety:"Use only the specified low-voltage educational supply. Check polarity before powering.",
    apparatus:["Breadboard","LED","330 Ω resistor","9V battery","Battery clip","Jumper wires","Multimeter"],
    steps:[["Place LED","Insert the LED with anode and cathode in separate rows.","led"],["Add resistor","Connect the resistor in series with the LED.","resistor"],["Connect supply","Connect the battery clip to the circuit.","battery"],["Check polarity","Verify the positive and negative connections.","polarity"],["Power","Complete the circuit and observe the LED.","power"]],engine:"led"},
  "s7-p4": {section:"Section 7",title:"Build a light-dependent resistor circuit",type:"Electronics Practical",
    safety:"Use the educational battery circuit only.",
    apparatus:["Breadboard","LDR","10 kΩ resistor","NPN transistor","LED","330 Ω resistor","9V battery","Jumper wires"],
    steps:[["Build sensor","Connect the LDR and 10 kΩ resistor divider.","sensor"],["Connect transistor","Connect the control junction to the transistor as specified.","transistor"],["Add LED","Connect the LED and 330 Ω resistor.","led"],["Change light","Vary ambient light in the simulator.","light"],["Observe","Record when the LED turns on/off.","observe"]],engine:"ldr"},
  "s7-p6": {section:"Section 7",title:"Build a simple audio amplifier",type:"Electronics Practical",
    safety:"Use the 9V educational supply and check the circuit before powering.",
    apparatus:["LM386","10 μF capacitors","0.047 μF capacitor","10 Ω resistor","1 kΩ resistor","10 kΩ potentiometer","8 Ω speaker","3.5 mm jack","9V battery","Breadboard"],
    steps:[["Place IC","Place the LM386 on the breadboard.","ic"],["Power","Connect the 9V supply as specified.","power"],["Input","Connect the audio input and volume control.","input"],["Output","Connect the speaker/output network.","output"],["Test","Play the signal and adjust volume.","test"]],engine:"amplifier"},
  "s8-p5": {section:"Section 8",title:"Identifying lifestyle diseases",type:"Fieldwork",
    safety:"Respect privacy and follow the health facility's instructions. Do not record confidential information.",
    apparatus:["Notebook","Pen","Interview schedule","Hand gloves","Nose mask"],
    steps:[["Prepare questions","Use the source interview questions.","questions"],["Collect evidence","Interview an appropriate resource person with permission.","interview"],["Record","Enter disease, causes, signs/symptoms, cure and prevention.","record"],["Analyse","Compare patterns in the community evidence.","analyse"],["Report","Prepare a concise class report.","conclude"]],engine:"lifestyle"},
  "s8-p6": {section:"Section 8",title:"Drugs and their negative effects",type:"Fieldwork",
    safety:"Use respectful, non-stigmatising language and follow the health facility's instructions.",
    apparatus:["Notebook","Pen","Interview schedule","Hand gloves","Nose mask"],
    steps:[["Prepare","Identify a health facility/resource person.","prepare"],["Interview","Ask about drug categories and effects.","interview"],["Record","Document evidence without personal identifiers.","record"],["Analyse","Classify effects and risks.","analyse"],["Report","Prepare findings for class discussion.","conclude"]],engine:"drugs"},
  "s9-p3": {section:"Section 9",title:"Making African black soap",type:"Production Practical",
    safety:"Teacher supervision is required. Handle heat, oils and ash safely and use protective equipment.",
    apparatus:["Plantain peels/cocoa pods","Shea butter","Palm oil","Coconut oil","Water","Pot","Mixing bowl","Spatula","Gloves","Goggles","Apron","Mould"],
    steps:[["Prepare ash","Dry and burn plant material to ash as directed.","ash"],["Prepare oils","Combine and gently heat the oils.","oils"],["Combine","Combine the soap components under supervision.","combine"],["Trace","Stir until the mixture reaches the described consistency.","trace"],["Mould","Pour into suitable moulds.","mould"],["Cure","Leave undisturbed to solidify and dry for the specified period.","cure"]],engine:"black_soap"},
  "s9-p4": {section:"Section 9",title:"Effect of potash source on local soap",type:"Production Practical",
    safety:"Perform under teacher supervision and use protective equipment. Avoid inhaling fumes.",
    apparatus:["Maize-stalk ash","Guinea-corn ash","Plantain-peel ash","Cocoa-pod ash","Oil-palm ash","Water","Palm oil","Receptacles","Scale","Measuring cylinders","Moulds"],
    steps:[["Prepare ashes","Prepare ash from the different plant materials.","ash"],["Make solutions","Prepare the different potash solutions as directed.","solution"],["Measure","Measure the required potash solution.","measure"],["Combine","Mix with palm oil under supervision.","combine"],["Mould","Pour the resulting paste into moulds.","mould"],["Compare","Compare the resulting soaps.","compare"]],engine:"potash_soap"},
  "s9-p5": {section:"Section 9",title:"Local gari production observation",type:"Fieldwork",
    safety:"Wear appropriate protective clothing and ask permission before taking photographs/videos.",
    apparatus:["Notebook","Pen","Pencil","Eraser","Goggles","Protective clothing","Camera/phone"],
    steps:[["Prepare visit","Identify a facility and arrange access.","prepare"],["Observe","Follow the process from harvesting/grating through processing.","observe"],["Interview","Ask questions about steps you do not understand.","interview"],["Map science","Connect stages to force, fermentation, filtration and heat transfer.","science"],["Report","Write the report using the source structure.","report"]],engine:"gari"}
};

const ENGINE = {
  starch: {
    data:()=>`<div class="instrument-row"><button data-act="sample">Place sample</button><button data-act="iodine">Apply iodine</button></div><div class="meter"><div id="simVisual" class="sample-tile">Sample</div></div>`,
    act:(a,s)=>{ if(a==="sample")s.observation="Sample placed on tile."; if(a==="iodine")s.observation="Iodine applied. Record the observed colour change."; }
  },
  solar_oven:{
    data:()=>`<div class="control-grid"><label>Reflector angle <input id="x1" type="range" min="0" max="90" value="45"></label><label>Insulation <input id="x2" type="range" min="0" max="100" value="50"></label><button data-act="measure">Measure temperature</button></div><div id="simVisual" class="oven-visual"></div>`,
    act:(a,s)=>{if(a==="measure"){let a=+x1.value,i=+x2.value;s.value=(30+a*.35+i*.18).toFixed(1);s.observation=`Temperature = ${s.value} °C`;}}
  },
  balloon_car:{
    data:()=>`<div class="control-grid"><label>Balloon size <input id="x1" type="range" min="20" max="100" value="60"></label><label>Car mass <input id="x2" type="range" min="20" max="100" value="50"></label><button data-act="run">Release car</button></div><div id="simVisual" class="track-visual"><div id="car">🚗</div></div>`,
    act:(a,s)=>{if(a==="run"){let b=+x1.value,m=+x2.value;s.value=Math.max(0,b*1.4-m*.5).toFixed(0);s.observation=`Distance = ${s.value} cm`;document.getElementById("car").style.transform=`translateX(${Math.min(85,+s.value)}%)`;}}
  },
  pendulum:{
    data:()=>`<div class="control-grid"><label>Length (m) <input id="x1" type="number" value="1" min=".1" step=".1"></label><label>Oscillations <input id="x2" type="number" value="10" min="1"></label><button data-act="time">Start stopwatch</button></div><div id="simVisual" class="pendulum-visual"><div class="string"></div><div class="bob">●</div></div>`,
    act:(a,s)=>{if(a==="time"){let l=+x1.value,n=+x2.value,T=2*Math.PI*Math.sqrt(l/9.8);s.value=(T*n).toFixed(2);s.observation=`${n} oscillations = ${s.value} s; period ≈ ${T.toFixed(2)} s`;}}
  },
  lustre:{
    data:()=>`<div class="control-grid"><select id="x1"><option>Iron</option><option>Copper</option><option>Aluminium</option><option>Gold</option><option>Silver</option></select><button data-act="light">Illuminate sample</button></div><div id="simVisual" class="metal-visual">Metal sample</div>`,
    act:(a,s)=>{if(a==="light"){s.observation=`Observe and rate the lustre of ${x1.value}.`;}}
  },
  hardness:{
    data:()=>`<div class="control-grid"><select id="x1"><option>Metal spoon</option><option>Key</option><option>Plastic ruler</option><option>Wood</option><option>Rubber band</option></select><button data-act="scratch">Scratch with coin</button></div><div id="simVisual" class="scratch-visual"></div>`,
    act:(a,s)=>{if(a==="scratch")s.observation=`Scratch test completed for ${x1.value}. Record whether a visible scratch formed.`;}
  },
  conductivity:{
    data:()=>`<div class="control-grid"><select id="x1"><option>Metal rod</option><option>Key</option><option>Wooden stick</option><option>Plastic ruler</option><option>Graphite rod</option></select><button data-act="test">Complete circuit</button></div><div id="simVisual" class="circuit-visual">🔋 ─── ◯ LED ───</div>`,
    act:(a,s)=>{if(a==="test"){let good=["Metal rod","Key","Graphite rod"].includes(x1.value);s.observation=`${x1.value}: ${good?"LED lights — conducting path":"LED does not light — poor/non-conducting path"}`;}}
  },
  diffusion:{
    data:()=>`<div class="control-grid"><label>Temperature <input id="x1" type="range" min="5" max="60" value="25"></label><button data-act="add">Add crystal</button><button data-act="wait">Advance time</button></div><div id="simVisual" class="diffusion-chamber"><div class="crystal"></div></div>`,
    act:(a,s)=>{if(a==="add")s.observation="Crystal placed at the bottom; do not stir."; if(a==="wait"){s.t=(s.t||0)+1;let spread=Math.min(90,s.t*(1+(+x1.value)/50)*14);document.querySelector(".diffusion-chamber").style.background=`radial-gradient(circle at 50% 85%, rgba(100,60,170,.9) ${spread}%, rgba(230,230,240,.8) ${Math.min(100,spread+8)}%)`;s.observation=`Diffusion time = ${s.t} min; estimated spread = ${spread.toFixed(0)}%`;}}
  },
  gas_diffusion:{
    data:()=>`<div class="control-grid"><button data-act="place">Open perfume</button><button data-act="wait">Advance 1 minute</button><label>Distance from source <input id="x1" type="range" min="1" max="20" value="5"></label></div><div id="simVisual" class="classroom-map"><span class="perfume-point">Perfume</span><span class="learner-point" id="lp">Learner</span></div>`,
    act:(a,s)=>{if(a==="place")s.observation="Perfume placed in one corner."; if(a==="wait"){s.t=(s.t||0)+1;s.observation=`At ${x1.value} m after ${s.t} min, record whether the scent is detected.`;}}
  },
  osmosis:{
    data:()=>`<div class="control-grid"><select id="x1"><option value="0">0% sucrose</option><option value="5">5% sucrose</option><option value="10">10% sucrose</option><option value="15">15% sucrose</option></select><input id="x2" type="number" value="8" placeholder="Initial circumference cm"><button data-act="immerse">Immerse</button><button data-act="wait">Advance 24 h</button></div><div id="simVisual" class="visking"><div class="tube"></div></div>`,
    act:(a,s)=>{if(a==="immerse")s.observation=`Model cell with ${x1.value} sucrose immersed in water.`;if(a==="wait"){let c=+x1.value,base=+x2.value;s.value=(base+c*.12).toFixed(2);s.observation=`Final circumference ≈ ${s.value} cm; compare with your recorded result.`;}}
  },
  potato_osmosis:{
    data:()=>`<div class="control-grid"><label>Sucrose <input id="x1" type="range" min="0" max="15" value="5"></label><label>Initial mass (g) <input id="x2" type="number" value="20"></label><button data-act="immerse">Immerse potato</button><button data-act="wait">Advance 24 h</button></div><div id="simVisual" class="potato-tank">🥔</div>`,
    act:(a,s)=>{if(a==="immerse")s.observation=`Potato placed in ${x1.value}% sucrose.`;if(a==="wait"){let c=+x1.value,m=+x2.value;s.value=Math.max(1,m*(1-(c-4)*.012)).toFixed(2);s.observation=`Final mass ≈ ${s.value} g.`;}}
  },
  pollination:{
    data:()=>`<div class="control-grid"><select id="x1"><option>Insect pollination</option><option>Wind pollination</option></select><button data-act="transfer">Transfer pollen</button></div><div id="simVisual" class="flower-visual">🌸 → ○</div>`,
    act:(a,s)=>{if(a==="transfer")s.observation=`${x1.value} simulated: identify the pollen source, transfer agent and stigma.`}
  },
  solar_panel:{
    data:()=>`<div class="control-grid"><select id="x1"><option>Direct sunlight</option><option>Partial shade</option><option>Artificial light</option></select><button data-act="measure">Read multimeter</button></div><div class="meter-board"><span id="voltageMeter">0.0 V</span><span id="currentMeter">0.00 A</span><span id="powerMeter">0.00 W</span></div>`,
    act:(a,s)=>{if(a==="measure"){let x=x1.value,v=x==="Direct sunlight"?5.8:x==="Partial shade"?3.4:1.8,i=x==="Direct sunlight"?.42:x==="Partial shade"?.22:.12,p=v*i;voltageMeter.textContent=v.toFixed(1)+" V";currentMeter.textContent=i.toFixed(2)+" A";powerMeter.textContent=p.toFixed(2)+" W";s.observation=`${x}: V=${v.toFixed(1)} V, I=${i.toFixed(2)} A, P=${p.toFixed(2)} W`;}}
  },
  friction:{
    data:()=>`<div class="control-grid"><label>Push force <input id="x1" type="range" min="1" max="20" value="10"></label><button data-act="smooth">Run smooth surface</button><button data-act="rough">Run rough surface</button></div><div id="simVisual" class="friction-track"><div id="block">■</div></div>`,
    act:(a,s)=>{if(a==="smooth"||a==="rough"){let f=+x1.value,d=a==="smooth"?f*8:f*3.5;s.value=d.toFixed(1);s.observation=`${a==="smooth"?"Smooth":"Rough"} surface distance = ${s.value} cm`;document.getElementById("block").style.transform=`translateX(${Math.min(85,d)}%)`;}}
  },
  gravity:{
    data:()=>`<div class="control-grid"><label>Mass (kg) <input id="x1" type="number" value="1" step=".1"></label><button data-act="measure">Measure gravitational force</button></div><div class="spring-scale">N <strong id="forceMeter">0.0</strong></div>`,
    act:(a,s)=>{if(a==="measure"){s.value=(+x1.value*9.8).toFixed(2);forceMeter.textContent=s.value;s.observation=`F = mg = ${s.value} N`;}}
  },
  velocity:{
    data:()=>`<div class="control-grid"><label>Ramp height (books) <input id="x1" type="range" min="1" max="8" value="2"></label><button data-act="release">Release toy car</button></div><div id="simVisual" class="ramp-visual"><div id="toycar">🚙</div></div>`,
    act:(a,s)=>{if(a==="release"){let h=+x1.value,time=Math.max(.35,1.7-.12*h),v=1/time;s.observation=`1 m track: time=${time.toFixed(2)} s; velocity=${v.toFixed(2)} m/s`;}}
  },
  cohesion:{
    data:()=>`<div class="control-grid"><select id="x1"><option>Plain water</option><option>Saltwater</option></select><button data-act="drop">Place droplet</button><button data-act="capillary">Test capillarity</button></div><div id="simVisual" class="drop-visual">●</div>`,
    act:(a,s)=>{if(a==="drop")s.observation=`Droplet test completed with ${x1.value}. Observe droplet shape/behaviour.`;if(a==="capillary")s.observation="Capillary test completed. Relate movement to adhesive and cohesive forces."}
  },
  led:{
    data:()=>`<div class="control-grid"><select id="x1"><option>Correct polarity</option><option>Reversed polarity</option></select><button data-act="power">Connect 9V supply</button></div><div id="simVisual" class="led-bench">🔋 ── Ω ── <span id="ledLight">●</span></div>`,
    act:(a,s)=>{if(a==="power"){let ok=x1.value==="Correct polarity";document.getElementById("ledLight").classList.toggle("lit",ok);s.observation=ok?"LED lights. Circuit polarity is correct.":"LED remains off. Check polarity.";}}
  },
  ldr:{
    data:()=>`<div class="control-grid"><label>Ambient light <input id="x1" type="range" min="0" max="100" value="30"></label><button data-act="power">Power circuit</button></div><div id="simVisual" class="ldr-bench">☀︎ → LDR → transistor → <span id="ldrLed">●</span></div>`,
    act:(a,s)=>{if(a==="power"){let l=+x1.value,on=l<45;document.getElementById("ldrLed").classList.toggle("lit",on);s.observation=`Light level ${l}%. LED ${on?"ON":"OFF"}.`}}
  },
  amplifier:{
    data:()=>`<div class="control-grid"><label>Volume <input id="x1" type="range" min="0" max="100" value="50"></label><button data-act="play">Play input signal</button></div><div id="simVisual" class="speaker-visual">🔊 <div id="wave"></div></div>`,
    act:(a,s)=>{if(a==="play"){let v=+x1.value;s.observation=`Audio signal played at ${v}% simulated volume. Adjust the potentiometer and observe the output.`;document.getElementById("wave").style.width=v+"%";}}
  },
  lifestyle:{
    data:()=>`<div class="field-form"><input id="x1" class="input" placeholder="Lifestyle disease"><input id="x2" class="input" placeholder="Cause"><input id="x3" class="input" placeholder="Signs/Symptoms"><input id="x4" class="input" placeholder="Prevention"><button data-act="record">Add interview record</button></div><div id="simVisual" class="field-board"></div>`,
    act:(a,s)=>{if(a==="record"){s.observation=`Recorded: ${x1.value} | Cause: ${x2.value} | Signs: ${x3.value} | Prevention: ${x4.value}`;document.getElementById("simVisual").innerHTML+=`<div class="field-record"><b>${esc(x1.value)}</b><br>Cause: ${esc(x2.value)}<br>Signs: ${esc(x3.value)}<br>Prevention: ${esc(x4.value)}</div>`;}}
  },
  drugs:{
    data:()=>`<div class="field-form"><select id="x1" class="input"><option>Therapeutic use</option><option>Recreational/non-medical use</option></select><input id="x2" class="input" placeholder="Observed effect/risk"><button data-act="record">Record evidence</button></div><div id="simVisual" class="field-board"></div>`,
    act:(a,s)=>{if(a==="record"){s.observation=`Evidence recorded: ${x1.value}; effect/risk: ${x2.value}`;document.getElementById("simVisual").innerHTML+=`<div class="field-record">${esc(x1.value)} — ${esc(x2.value)}</div>`;}}
  },
  black_soap:{
    data:()=>`<div class="control-grid"><button data-act="ash">Prepare ash</button><button data-act="oils">Prepare oils</button><button data-act="combine">Combine</button><button data-act="trace">Reach trace</button><button data-act="mould">Mould</button><button data-act="cure">Cure</button></div><div id="simVisual" class="soap-line"><span id="soapFill"></span></div>`,
    act:(a,s)=>{let map={ash:1,oils:2,combine:3,trace:4,mould:5,cure:6};if(map[a]){s.t=Math.max(s.t||0,map[a]);document.getElementById("soapFill").style.width=(s.t/6*100)+"%";s.observation=`Soap production stage: ${a}.`;}}
  },
  potash_soap:{
    data:()=>`<div class="control-grid"><select id="x1"><option>Maize stalk ash</option><option>Guinea corn stalk ash</option><option>Plantain peel ash</option><option>Cocoa pod ash</option><option>Oil palm spike leaflet ash</option></select><button data-act="compare">Compare source</button></div><div id="simVisual" class="soap-compare"></div>`,
    act:(a,s)=>{if(a==="compare"){s.observation=`Selected potash source: ${x1.value}. Record the observed soap characteristics and compare with the other sources.`}}
  },
  gari:{
    data:()=>`<div class="control-grid"><button data-act="harvest">Harvest</button><button data-act="grate">Grate</button><button data-act="ferment">Ferment</button><button data-act="dewater">Dewater</button><button data-act="roast">Roast</button><button data-act="sieve">Sieve</button></div><div id="simVisual" class="process-line"></div>`,
    act:(a,s)=>{s.t=(s.t||[]);s.t.push(a);s.observation=`Gari stage completed: ${a}. Connect it to the scientific principle described in the learning material.`;document.getElementById("simVisual").innerHTML=s.t.map((x,i)=>`<span class="process-stage">${i+1}. ${x}</span>`).join("");}
  }
};

function esc(x){return String(x??"").replace(/[&<>"']/g,m=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[m]));}

let currentLab=null, labState={step:0,done:0,score:0,observation:"",value:"",t:0,notes:""};

async function loadPracticalStudio(){
  const list=document.getElementById("practicalList");
  if(!list)return;
  let response;
  try{response=await api("/api/practicals")}catch(e){response={practicals:Object.entries(LABS).map(([id,x])=>({id,...x}))}}
  const items=(response.practicals||[]).filter(x=>LABS[x.id]);
  items.forEach(item=>{LABS[item.id].alignment=item.alignment||LABS[item.id].alignment});
  const render=arr=>list.innerHTML=arr.map(x=>`<button class="lab-item" onclick="openLab('${x.id}')"><span>${esc(LABS[x.id].section)}</span><b>${esc(LABS[x.id].title)}</b><small>${esc(LABS[x.id].type)}</small></button>`).join("");
  render(items);
  const initialLab=decodeURIComponent(location.hash.slice(1));if(initialLab&&LABS[initialLab])setTimeout(()=>openLab(initialLab),0);
  document.getElementById("practicalSearch").oninput=e=>render(items.filter(x=>(LABS[x.id].title+" "+LABS[x.id].section).toLowerCase().includes(e.target.value.toLowerCase())));
  window.openLab=openLab;
  document.getElementById("resetLab").onclick=()=>currentLab&&openLab(currentLab);
  document.getElementById("prevStep").onclick=()=>changeStep(-1);
  document.getElementById("nextStep").onclick=()=>changeStep(1);
  document.getElementById("performStep").onclick=performStep;
  document.getElementById("saveRecord").onclick=saveLabRecord;
}
function openLab(id){
  currentLab=id; labState={step:0,done:0,score:0,observation:"",value:"",t:0,notes:""};
  const l=LABS[id];document.getElementById("labEmpty").hidden=true;document.getElementById("labView").hidden=false;
  labTitle.textContent=l.title;labSubtitle.textContent="Perform the investigation, capture evidence and explain your conclusion.";
  labSection.textContent=l.section;labType.textContent=l.type; safetyText.textContent=l.safety;
  const align=l.alignment||{classification:"Extension / enrichment",note:"Curriculum mapping has not yet been verified from the supplied source PDF."};
  document.getElementById("labAlignment").innerHTML=align.learning_indicator_code?`<div class="alignment-status official">Curriculum requirement</div><div><b>${esc(align.learning_indicator_code)}</b><p>${esc(align.objective)}</p><small>Verified source: supplied General Science Curriculum PDF, p. ${esc(align.source_page)}</small></div>`:`<div class="alignment-status extension">Extension / enrichment</div><div><b>Mapping pending verification</b><p>${esc(align.note)}</p><small>This practical is not presented as an official curriculum requirement.</small></div>`;
  apparatus.innerHTML=l.apparatus.map((x,i)=>`<div class="apparatus-item" draggable="true" data-name="${esc(x)}"><span class="apparatus-icon">⚙</span><span>${esc(x)}</span><button onclick="placeApparatus('${esc(x).replace(/'/g,"\\'")}')">Use</button></div>`).join("");
  bench.innerHTML=`<div class="bench-grid"><div id="benchObjects"></div><div class="bench-surface"><span>WORKBENCH</span></div></div>`;
  const e=ENGINE[l.engine]||{data:()=>"<p>Interactive bench is being configured.</p>",act:()=>{}};
  instrumentPanel.innerHTML=e.data();
  instrumentPanel.querySelectorAll("[data-act]").forEach(b=>b.onclick=()=>runAction(b.dataset.act));
  renderStep(); renderData(); renderAssessment();
}
window.placeApparatus=function(name){const box=document.getElementById("benchObjects");box.innerHTML+=`<span class="bench-object">${esc(name)}</span>`;benchState.textContent="Apparatus placed";}
function renderStep(){
  const l=LABS[currentLab],st=l.steps[labState.step];stepCounter.textContent=`Step ${labState.step+1} of ${l.steps.length}`;progressBar.style.width=((labState.step)/Math.max(1,l.steps.length-1)*100)+"%";
  procedure.innerHTML=`<div class="step-card"><div class="step-number">${labState.step+1}</div><div><h3>${esc(st[0])}</h3><p>${esc(st[1])}</p><div class="step-tag">Action required: ${esc(st[2])}</div></div></div>`;
  prevStep.disabled=labState.step===0;nextStep.disabled=labState.step>=l.steps.length-1;
  procedureState.textContent=labState.done>labState.step?"Completed":"Current step";
}
function performStep(){
  const l=LABS[currentLab],e=l.steps[labState.step];labState.done=Math.max(labState.done,labState.step+1);labState.score=Math.round(labState.done/l.steps.length*100);
  labState.observation=labState.observation||`Step completed: ${e[0]}.`;
  labState.score=Math.min(100,labState.score+Math.min(5,labState.done));
  labScore.textContent=`Score: ${labState.score}%`;benchState.textContent=`Step ${labState.step+1} performed`;renderData();renderAssessment();
}
function changeStep(d){const n=labState.step+d;if(n>=0&&n<LABS[currentLab].steps.length){labState.step=n;renderStep();}}
function runAction(action){
  const e=ENGINE[LABS[currentLab].engine];if(!e)return; e.act(action,labState);labState.score=Math.min(100,labState.score+4);labScore.textContent=`Score: ${labState.score}%`;renderData();
}
function renderData(){
  dataCapture.innerHTML=`<div class="live-reading"><span>Latest observation</span><b>${esc(labState.observation||"No observation recorded yet.")}</b>${labState.value?`<em>Measured value: ${esc(labState.value)}</em>`:""}</div>`;
  if(labState.notes)notes.value=labState.notes;
}
function renderAssessment(){
  const l=LABS[currentLab],complete=labState.done>=l.steps.length;
  assessmentState.textContent=complete?"Practical completed — submit your evidence.":"Complete all practical steps to unlock submission.";
  assessment.innerHTML=complete?`<div class="assessment-card"><h3>Practical submission</h3><p>Use your observations and measurements to answer the following.</p><label>What did you observe?<textarea class="textarea" id="a1"></textarea></label><label>What evidence supports your conclusion?<textarea class="textarea" id="a2"></textarea></label><label>What would you improve in the investigation?<textarea class="textarea" id="a3"></textarea></label><button class="primary" onclick="submitAssessment()">Submit practical</button><div id="submissionResult"></div></div>`:`<div class="locked-assessment">🔒 Complete the procedure steps and record evidence to unlock the assessment.</div>`;
}
window.submitAssessment=function(){labState.score=Math.max(labState.score,85);labScore.textContent=`Score: ${labState.score}%`;document.getElementById("submissionResult").innerHTML=`<div class="result success">Practical submitted. Evidence recorded. Teacher review can use the observation and assessment responses.</div>`;assessmentState.textContent="Submitted";}
function saveLabRecord(){labState.notes=notes.value;localStorage.setItem("v4lab:"+currentLab,JSON.stringify(labState));benchState.textContent="Record saved";}

document.addEventListener("DOMContentLoaded",loadPracticalStudio);

async function loadPracticalDesigner(){
 const form=document.getElementById("practicalDesigner");if(!form)return;const indicator=document.getElementById("practicalIndicator"),status=document.getElementById("practicalDesignerStatus");
 try{const x=await api("/api/curriculum");indicator.innerHTML='<option value="">Select a verified indicator</option>'+x.data.map(r=>`<option value="${r.indicator_id}">${esc(r.indicator_code)} — ${esc(r.indicator_description)}</option>`).join("");form.onsubmit=async e=>{e.preventDefault();const raw=Object.fromEntries(new FormData(form));try{const x=await api("/api/practical-designs",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(raw)});status.textContent=`Practical design #${x.id} saved with curriculum alignment.`;form.reset()}catch(err){status.textContent=err.message}}}catch(e){status.textContent="Unable to load verified learning indicators."}
}
document.addEventListener("DOMContentLoaded",loadPracticalDesigner);

async function loadAssignment(){
 const form=document.getElementById("submissionForm");if(!form)return;
 const id=location.pathname.split("/").pop();
 try{const x=await api(`/api/assignments/${id}`),a=x.assignment;
   document.getElementById("atitle").textContent=a.title;
   document.getElementById("ameta").textContent=`${a.course_title} · ${a.max_points} points${a.due_at?` · Due ${a.due_at}`:""}`;
   document.getElementById("ainstructions").textContent=a.instructions||"";
   const t=document.getElementById("answerText");
   if(x.submission){t.value=x.submission.answer_text||"";if(x.submission.status==='graded'){form.innerHTML=`<div class="result success"><b>Graded: ${esc(x.submission.score)}/${esc(a.max_points)}</b><p>${esc(x.submission.feedback||"No written feedback was provided.")}</p></div>`;}}
   else form.onsubmit=async e=>{e.preventDefault();try{await api(`/api/assignments/${id}/submit`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({answer_text:t.value})});document.getElementById("submissionStatus").textContent="Assignment submitted successfully.";t.disabled=true;e.target.querySelector("button").disabled=true}catch(err){document.getElementById("submissionStatus").textContent=err.message}};
 }catch(e){document.getElementById("submissionPanel").innerHTML=`<div class="panel lesson-loading">${esc(e.message)}</div>`}
}
document.addEventListener("DOMContentLoaded",loadAssignment);
