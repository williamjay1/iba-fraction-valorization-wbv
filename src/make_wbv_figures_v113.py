"""Redesign verified WBV figures with physical layout and vector collision QA.

Data/model values are unchanged from the v112 revision. All outputs are new v113
files. Original SciencePlots MIT style files are loaded before explicit Nature-
inspired accessibility overrides (Arial, final >=8 pt main labels, fixed canvas).
Install the declared graphics dependencies and a legally obtained Arial font.
No TeX, network access or local Python-library fallback is used.
"""
from pathlib import Path
import csv
import hashlib
import json
import math
import os
import re
import shutil
import sys
import warnings
import xml.etree.ElementTree as ET

import numpy as np
CONFIG_ROOT=Path(os.environ.get("PROJECT30_WORK",Path(__file__).resolve().parent.parent))
MPL_CACHE=CONFIG_ROOT/"temp/mpl_wbv_v113"
MPL_CACHE.mkdir(parents=True,exist_ok=True)
os.environ["MPLCONFIGDIR"]=str(MPL_CACHE)
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.lines import Line2D
from matplotlib.markers import MarkerStyle
from matplotlib.patches import Rectangle, Polygon
from matplotlib.transforms import Affine2D, Bbox
from matplotlib.path import Path as MplPath
from pypdf import PdfReader
from PIL import Image

ROOT = Path(os.environ.get("PROJECT30_WORK", Path(__file__).resolve().parent.parent))
OUT = ROOT / "results/wbv_v113/figures"
DATA = ROOT / "results/wbv_v113/figure_data"
STYLES = ROOT / "results/wbv_v113/third_party/scienceplots"
OUT.mkdir(parents=True, exist_ok=True)
DATA.mkdir(parents=True, exist_ok=True)

STYLE_FILES = [STYLES / name for name in
               ("science.mplstyle", "no-latex.mplstyle", "nature.mplstyle")]
for path in STYLE_FILES:
    assert path.is_file(), f"Original vendored style missing: {path}"
plt.style.use([str(p) for p in STYLE_FILES])

# Original science/no-latex/nature styles are used first. These overrides are
# required by this task: larger labels, Windows Arial, no TeX, fixed print canvas,
# editable vector text, and 1200 dpi ONLY for the native raster export.
OVERRIDES = {
    "font.family": "sans-serif", "font.sans-serif": ["Arial"],
    "font.size": 9.2, "axes.labelsize": 9.2, "axes.titlesize": 9.5,
    "xtick.labelsize": 9.2, "ytick.labelsize": 9.2,
    "text.usetex": False, "mathtext.fontset": "dejavusans",
    "axes.edgecolor": "#252525", "axes.labelcolor": "#252525",
    "text.color": "#252525", "xtick.color": "#252525", "ytick.color": "#252525",
    "axes.linewidth": .5, "axes.spines.top": False,
    "axes.spines.right": False, "axes.grid": False,
    "xtick.minor.visible": False, "ytick.minor.visible": False,
    "xtick.top": False, "ytick.right": False,
    "xtick.major.size": 2.5, "ytick.major.size": 2.5,
    "xtick.major.width": .5, "ytick.major.width": .5,
    "lines.linewidth": 1., "lines.markersize": 3.5,
    "legend.frameon": False, "legend.fontsize": 9.2,
    "pdf.fonttype": 42, "ps.fonttype": 42, "svg.fonttype": "none",
    "savefig.bbox": None, "savefig.pad_inches": 0,
    "savefig.facecolor": "white", "figure.facecolor": "white",
    "figure.dpi": 300, "axes.unicode_minus": True,
}
plt.rcParams.update(OVERRIDES)
# A missing scientific glyph must stop production, not silently become a box.
warnings.filterwarnings("error",message=r"Glyph .* missing from font.*",category=UserWarning)
try:
    ARIAL = Path(font_manager.findfont(font_manager.FontProperties(family="Arial"),
                                      fallback_to_default=False))
except ValueError as exc:
    raise RuntimeError("Arial is required to reproduce these figure layouts. Install a legally obtained Arial font; fonts are not distributed with this repository.") from exc
BLUE, ORANGE, GREEN = "#0072B2", "#D55E00", "#009E73"
INK, GRAY, LIGHT = "#252525", "#777777", "#D5D5D5"
PALE_ORANGE = "#F8EAE2"

FILES = {
    "german_streams": ROOT / "results/quality_conditioned_credit_v110/stream_credit_decomposition.csv",
    "german_bounds": ROOT / "results/mass_only_identification_v112/mass_only_budget_bounds.csv",
    "german_break_even": ROOT / "results/mass_only_identification_v112/mass_only_break_even_intervals.csv",
    "italian_samples": ROOT / "results/same_material_v114/mantovani_joint_samples.csv",
    "spanish_samples": ROOT / "results/same_material_v114/spain_joint_samples.csv",
    "swedish_grid": ROOT / "results/sweden_qualification_order_v111/qualification_order_grid.csv",
}

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def read(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))

def write_csv(name, rows):
    assert rows
    with (DATA / name).open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

def fig_text(fig, x, y, text, **kwargs):
    kwargs.setdefault("fontsize", 9.2)
    kwargs.setdefault("va", "center")
    artist = fig.text(x, y, text, **kwargs)
    artist.set_gid("label:" + text.replace("\n", " / "))
    return artist

def panel_heading(fig, letter, title, x, y):
    fig_text(fig, x, y, letter, fontweight="bold", fontsize=10.)
    fig_text(fig, x + .044, y, title, fontsize=9.5)

def fig_line(fig, xs, ys, **kwargs):
    line = Line2D(xs, ys, transform=fig.transFigure, clip_on=False, **kwargs)
    fig.add_artist(line)
    return line

def expanded(box, pixels):
    return Bbox.from_extents(box.x0-pixels, box.y0-pixels,
                            box.x1+pixels, box.y1+pixels)

def intersect_box(a, b):
    if not a.overlaps(b):
        return None
    return Bbox.from_extents(max(a.x0,b.x0), max(a.y0,b.y0),
                            min(a.x1,b.x1), min(a.y1,b.y1))

def line_segments(path):
    """Flatten stroke vertices for deterministic rectangle/segment tests."""
    previous = start = None
    for points, code in path.iter_segments(curves=False, simplify=False):
        point = np.asarray(points[-2:], dtype=float)
        if not np.all(np.isfinite(point)):
            previous = start = None
        elif code == MplPath.MOVETO:
            previous = start = point
        elif code == MplPath.CLOSEPOLY:
            if previous is not None and start is not None:
                yield previous, start
            previous = None
        elif previous is not None:
            yield previous, point
            previous = point

def segment_hits_box(p, q, box):
    # Liang-Barsky segment clipping. Testing an expanded text box accounts for
    # stroke thickness; dashed paths are conservatively treated as solid.
    dx, dy = q-p
    t0, t1 = 0., 1.
    for direction, distance in [(-dx,p[0]-box.x0),(dx,box.x1-p[0]),
                                (-dy,p[1]-box.y0),(dy,box.y1-p[1])]:
        if abs(direction)<1e-12:
            if distance<0:
                return False
        else:
            value=distance/direction
            if direction<0:
                t0=max(t0,value)
            else:
                t1=min(t1,value)
            if t0>t1:
                return False
    return True

def path_hits_box(path, box, filled=False, stroke_px=0.):
    if filled and path.intersects_bbox(box, filled=True):
        return True
    padded=expanded(box,stroke_px)
    return any(segment_hits_box(p,q,padded) for p,q in line_segments(path))

def collision_audit(fig, name, require_pass=True, report_dir=None):
    """Check actual renderer geometry, including title/tick Text objects.

    Only figure and Axes white background rectangles are excluded, as documented
    containers. Tick LABELS are included in text-text tests. Actual major/minor
    tick STROKES, visible grid strokes, and visible spines are included in text-
    graphics tests. Data clipping is respected, so a tick label outside the Axes
    is not falsely said to touch an invisible extension of the plotted data.
    No text/data, annotation, or arbitrary Axes-area overlap is whitelisted.
    """
    fig.canvas.draw()
    renderer=fig.canvas.get_renderer()
    all_text=[]; seen=set()
    for artist in fig.findobj(match=matplotlib.text.Text):
        if id(artist) in seen:
            continue
        seen.add(id(artist))
        if artist.get_visible() and artist.get_text().strip():
            box=artist.get_window_extent(renderer)
            if box.width>0 and box.height>0:
                all_text.append((artist,box))
    outer=[]; pairs=[]; crossings=[]
    for artist,box in all_text:
        if box.x0<-.5 or box.y0<-.5 or box.x1>fig.bbox.width+.5 or box.y1>fig.bbox.height+.5:
            outer.append(artist.get_text())
    for index,(a,abox) in enumerate(all_text):
        for b,bbox in all_text[index+1:]:
            overlap=intersect_box(abox,bbox)
            if overlap is not None and overlap.width>.35 and overlap.height>.35:
                pairs.append({"first":a.get_text(),"second":b.get_text(),
                              "overlap_pixels":[overlap.width,overlap.height]})

    backgrounds={id(fig.patch)} | {id(ax.patch) for ax in fig.axes}
    graphics=[]
    for artist in fig.findobj():
        if not artist.get_visible() or id(artist) in backgrounds:
            continue
        if isinstance(artist,Line2D):
            path=artist.get_path().transformed(artist.get_transform())
            stroke=artist.get_linestyle() not in ("None","none","",None)
            if stroke:
                graphics.append((artist,path,False,artist.get_linewidth()*fig.dpi/144.,"line"))
            marker=artist.get_marker()
            if marker not in ("None","none","",None," "):
                marker_style=MarkerStyle(marker)
                marker_path=marker_style.get_path().transformed(marker_style.get_transform())
                marker_scale=artist.get_markersize()*fig.dpi/72.
                centers=artist.get_transform().transform(artist.get_path().vertices)
                for center in centers:
                    if np.all(np.isfinite(center)):
                        mpath=marker_path.transformed(Affine2D().scale(marker_scale).translate(*center))
                        filled=marker_style.is_filled()
                        graphics.append((artist,mpath,filled,
                                         artist.get_markeredgewidth()*fig.dpi/144.,"marker"))
        elif isinstance(artist,matplotlib.patches.Patch):
            path=artist.get_path().transformed(artist.get_transform())
            filled=bool(artist.get_fill() and artist.get_facecolor()[3]>0)
            edge=artist.get_edgecolor()[3]>0
            graphics.append((artist,path,filled,
                             artist.get_linewidth()*fig.dpi/144. if edge else 0.,
                             "filled-data-patch" if filled else "patch-stroke"))

    for text,box in all_text:
        for artist,path,filled,width,kind in graphics:
            testbox=box
            clipbox=artist.get_clip_box() if artist.get_clip_on() else None
            if clipbox is not None:
                testbox=intersect_box(testbox,clipbox)
                if testbox is None:
                    continue
            if path_hits_box(path,testbox,filled=filled,stroke_px=width):
                crossings.append({"text":text.get_text(),"graphic_kind":kind,
                                  "graphic_gid":artist.get_gid(),
                                  "text_bbox_pixels":[box.x0,box.y0,box.x1,box.y1]})
    # No Collection artists are used: lines/markers and filled Polygon/Rectangle
    # patches are deliberately explicit, allowing complete deterministic scans.
    visible_collections=[c for ax in fig.axes for c in ax.collections if c.get_visible()]
    assert not visible_collections, "Unscanned Collection; add geometry support before exporting"
    report={"figure":name,"audit_renderer_dpi":fig.dpi,
            "text_objects_checked":len(all_text),"graphic_paths_checked":len(graphics),
            "canvas_overflows":outer,"text_text_intersections":pairs,
            "text_graphics_intersections":crossings,
            "exclusions":["Figure and Axes white background containers only"],
            "axis_policy":"Tick labels, major/minor tick strokes, visible grid lines and spines are checked; actual Axes clip boxes are respected.",
            "filled_region_policy":"Actual filled data paths are tested, not only bounding boxes.",
            "stroke_policy":"Stroke half-width is included; dashed lines are conservatively tested as continuous segments.",
            "status":"PASS" if not (outer or pairs or crossings) else "FAIL"}
    destination=DATA if report_dir is None else report_dir
    destination.mkdir(parents=True,exist_ok=True)
    (destination/f"{name}_collision_audit.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    if require_pass and report["status"]!="PASS":
        raise RuntimeError(f"Layout collision in {name}: {json.dumps(report,ensure_ascii=False)}")
    return report

def collision_positive_controls():
    """Confirm the guard detects independent known-bad geometry classes."""
    reports=[]
    directory=DATA/"collision_detector_positive_controls"
    for category in ["text_text","line_crossing","filled_region","marker_crossing"]:
        fig=plt.figure(figsize=(3,2),dpi=300)
        fig_text(fig,.5,.5,"Control label",ha="center")
        if category=="text_text":
            fig_text(fig,.5,.5,"Overlapping text",ha="center")
        elif category=="line_crossing":
            fig_line(fig,[.2,.8],[.5,.5],lw=1.,color=BLUE)
        elif category=="filled_region":
            fig.add_artist(Rectangle((.35,.35),.3,.3,transform=fig.transFigure,
                                     facecolor=BLUE,edgecolor="none",clip_on=False))
        else:
            fig_line(fig,[.5],[.5],marker="o",ms=7,mfc=BLUE,mec=BLUE,ls="None")
        report=collision_audit(fig,category,require_pass=False,report_dir=directory)
        assert report["status"]=="FAIL",f"Positive control missed: {category}"
        if category=="text_text":
            assert report["text_text_intersections"]
        else:
            assert report["text_graphics_intersections"]
        reports.append({"control":category,"known_bad_layout_detected":True})
        plt.close(fig)
    (directory/"summary.json").write_text(json.dumps({"status":"PASS","controls":reports,
                              "note":"Expected FAIL layouts verify detector sensitivity; these are not manuscript figures."},indent=2),encoding="utf-8")
    return reports

def vector_audit(path):
    reader=PdfReader(path)
    images=[]; fonts=[]
    def inspect(resources):
        resources=resources.get_object()
        for key,reference in resources.get("/XObject",{}).items():
            obj=reference.get_object()
            if obj.get("/Subtype")=="/Image":
                images.append(str(key))
            elif "/Resources" in obj:
                inspect(obj["/Resources"])
        for key,reference in resources.get("/Font",{}).items():
            font=reference.get_object()
            descendants=font.get("/DescendantFonts",[])
            check=descendants[0].get_object() if descendants else font
            descriptor=check.get("/FontDescriptor",{})
            descriptor=descriptor.get_object() if hasattr(descriptor,"get_object") else descriptor
            fonts.append({"resource":str(key),"base_font":str(font.get("/BaseFont")),
                          "subtype":str(font.get("/Subtype")),
                          "descendant_subtype":str(check.get("/Subtype")),
                          "font_embedded":any(k in descriptor for k in ("/FontFile","/FontFile2","/FontFile3"))})
    for page in reader.pages:
        inspect(page["/Resources"])
    svg=path.with_suffix(".svg")
    xml=ET.parse(svg).getroot()
    svg_images=sum(el.tag.endswith("}image") for el in xml.iter())
    svg_text=sum(el.tag.endswith("}text") for el in xml.iter())
    svg_paths=sum(el.tag.endswith("}path") for el in xml.iter())
    assert not images and not svg_images, "Raster image unexpectedly embedded in vector export"
    assert fonts and all(f["font_embedded"] and f["subtype"]!="/Type3" for f in fonts)
    assert svg_text>0 and svg_paths>0
    assert "Arial" in svg.read_text(encoding="utf-8")
    return {"pdf_image_objects":len(images),"pdf_fonts":fonts,
            "svg_image_elements":svg_images,"svg_text_elements":svg_text,
            "svg_path_elements":svg_paths,
            "status":"PASS: vectors retained; embedded non-Type3 fonts; editable SVG text"}

GEOMETRY=[]
POSITIVE_CONTROLS=collision_positive_controls()
def save(fig,name,description):
    report=collision_audit(fig,name)
    for ext in ("pdf","svg"):
        fig.savefig(OUT/f"{name}.{ext}",bbox_inches=None)
    fig.savefig(OUT/f"{name}.png",dpi=1200,bbox_inches=None)
    fig.savefig(OUT/f"{name}_print_preview.png",dpi=300,bbox_inches=None)
    vectors=vector_audit(OUT/f"{name}.pdf")
    with Image.open(OUT/f"{name}.png") as raster:
        pixel_dimensions=list(raster.size)
        dpi=raster.info.get("dpi")
    min_font=min(t.get_fontsize() for t in fig.findobj(match=matplotlib.text.Text)
                 if t.get_visible() and t.get_text().strip())
    GEOMETRY.append({"figure":name,"width_cm":fig.get_figwidth()*2.54,
                     "height_cm":fig.get_figheight()*2.54,"raster_dpi":1200,
                     "raster_pixel_dimensions":pixel_dimensions,"png_dpi_metadata":dpi,
                     "preview_dpi":300,"minimum_text_size_pt":min_font,
                     "layout_audit":report["status"],"vector_audit":vectors,
                     "description":description})
    plt.close(fig)

SCENARIOS=["laboratory_scale_2023","high_ambition_2030","worst_case_2030"]
LABELS=["Laboratory 2023","High ambition 2030","Worst case 2030"]
streams=read(FILES["german_streams"])
bounds=read(FILES["german_bounds"])
intervals=read(FILES["german_break_even"])

# Figure 1: paired fine-fraction shares replace the stacked mass/credit table.
fig=plt.figure(figsize=(18/2.54,11.1/2.54))
panel_heading(fig,"a","Fine fraction: mass versus direct credit",.038,.957)
fig_line(fig,[.637],[.957],marker="o",markersize=4.2,mfc="white",mec=GRAY,ls="None")
fig_text(fig,.655,.957,"Mass",fontsize=9.2)
fig_line(fig,[.79],[.957],marker="o",markersize=4.2,mfc=BLUE,mec=BLUE,ls="None")
fig_text(fig,.807,.957,"Direct credit",fontsize=9.2)
ax=fig.add_axes([.23,.665,.715,.235])
shares=[]
for index,scenario in enumerate(SCENARIOS):
    rows=[r for r in streams if r["source_scenario"]==scenario]
    fine=next(r for r in rows if r["stream"]=="fine")
    total_mass=sum(float(r["mass_kg_per_FU"]) for r in rows)
    total_credit=sum(float(r["export_reconciled_credit_kg_CO2eq_per_FU"]) for r in rows)
    mass=100*float(fine["mass_kg_per_FU"])/total_mass
    credit=100*float(fine["export_reconciled_credit_kg_CO2eq_per_FU"])/total_credit
    y=2-index
    ax.plot([mass,credit],[y,y],color=LIGHT,lw=.8,zorder=1)
    ax.plot([mass],[y],marker="o",ms=4.4,mfc="white",mec=GRAY,mew=.9,ls="None",zorder=2)
    ax.plot([credit],[y],marker="o",ms=4.4,mfc=BLUE,mec=BLUE,ls="None",zorder=2)
    for value,color in [(mass,GRAY),(credit,BLUE)]:
        ax.text(value,y+.235,f"{value:.1f}",ha="center",va="bottom",fontsize=9.2,color=color)
    shares.append({"scenario":scenario,"mass_total_kg_per_source_Mg":total_mass,
                   "direct_credit_total_kgCO2eq_per_source_Mg":total_credit,
                   "fine_mass_share_percent":mass,"fine_direct_credit_share_percent":credit,
                   "medium_mass_share_percent":100-mass,"medium_direct_credit_share_percent":100-credit,
                   "source_csv":FILES["german_streams"].relative_to(ROOT).as_posix()})
ax.set_xlim(50,78);ax.set_ylim(-.55,2.7)
ax.set_yticks([2,1,0],LABELS);ax.tick_params(axis="y",length=0,pad=9)
ax.set_xticks([50,60,70]);ax.set_xlabel("Fine-fraction share (%)",labelpad=5)
ax.spines["left"].set_visible(False)
fig_text(fig,.038,.544,"Accepted-mass climate bounds",fontsize=9.5)
for index,(scenario,title,left) in enumerate(zip(SCENARIOS,LABELS,[.115,.418,.721])):
    ax=fig.add_axes([left,.187,.242,.272])
    rows=[r for r in bounds if r["source_scenario"]==scenario]
    x=np.array([100*float(r["accepted_mass_fraction_of_clinker_streams"]) for r in rows])
    lo=np.array([float(r["lower_Delta_max"]) for r in rows])
    hi=np.array([float(r["upper_Delta_max"]) for r in rows])
    inter=next(r for r in intervals if r["source_scenario"]==scenario)
    start=100*float(inter["possible_break_even_fraction_of_clinker_mass"])
    end=100*float(inter["guaranteed_break_even_fraction_of_clinker_mass"])
    ax.add_patch(Rectangle((start,-46),end-start,142,facecolor=PALE_ORANGE,edgecolor="none",zorder=0))
    ax.plot(x,hi,color=BLUE,lw=1.)
    ax.plot(x,lo,color=ORANGE,lw=1.,ls=(0,(4,2.5)))
    ax.axhline(0,color=GRAY,lw=.5,zorder=1)
    ax.set_xlim(0,100);ax.set_ylim(-46,96)
    ax.set_xticks([0,50,100]);ax.set_yticks([-40,0,40,80])
    ax.set_xlabel("Accepted mass (%)",labelpad=5)
    if index:
        ax.tick_params(labelleft=False)
    else:
        ax.set_ylabel("Climate margin M\n(kg CO$_2$-eq per source Mg)",labelpad=7)
    fig_text(fig,left-.023,.492,"bcd"[index],fontsize=10.,fontweight="bold")
    fig_text(fig,left+.121,.492,title,ha="center",fontsize=9.2)
for x,label,color,style in [(.15,"Fine-first",BLUE,"-"),(.40,"Medium-first",ORANGE,"--")]:
    fig_line(fig,[x,x+.04],[.057,.057],color=color,lw=1.,ls=style)
    fig_text(fig,x+.052,.057,label)
rect=Rectangle((.715,.042),.029,.030,transform=fig.transFigure,
               facecolor=PALE_ORANGE,edgecolor="none",clip_on=False)
fig.add_artist(rect)
fig_text(fig,.756,.057,"Either sign (Δ = 0)")
save(fig,"figure1_mass_credit_margin","Paired fine-stream shares plus three deterministic accepted-mass margin facets.")
write_csv("figure1_mass_credit_shares.csv",shares)
shutil.copyfile(FILES["german_bounds"],DATA/"figure1_mass_margin_bounds.csv")
shutil.copyfile(FILES["german_break_even"],DATA/"figure1_mass_break_even.csv")

# Figure 2: all source records retained; maxima emphasized by a ring rather than
# a large star that obscures the observed marker. No error bars are invented.
italian=read(FILES["italian_samples"])
plants=["PR","PC","TO","FE","FC"]
fig=plt.figure(figsize=(18/2.54,11.6/2.54))
ticks=["0.063–\n0.2","0.2–\n0.3","0.3–\n0.5","0.5–\n1","1–\n2"]
ranking=[]
for index,plant in enumerate(plants):
    col=index%3;row=index//3
    left=[.105,.410,.715][col];bottom=[.575,.150][row]
    ax=fig.add_axes([left,bottom,.255,.292])
    rows=[r for r in italian if r["plant"]==plant]
    oxide=np.array([float(r["oxide_only_CO2_ceiling_kg_per_Mg_fraction"]) for r in rows])
    corrected=np.array([float(r["carbonate_corrected_CO2_ceiling_kg_per_Mg_fraction"]) for r in rows])
    x=np.arange(5)
    ax.plot(x,oxide,color=GRAY,marker="o",mfc="white",mec=GRAY,ms=3.6,lw=.8)
    ax.plot(x,corrected,color=BLUE,marker="s",mfc=BLUE,mec=BLUE,ms=3.4,lw=1.)
    imax,jmax=int(np.argmax(oxide)),int(np.argmax(corrected))
    for winner,values in [(imax,oxide),(jmax,corrected)]:
        ax.plot([winner],[values[winner]],marker="o",ms=7.1,mfc="none",mec=ORANGE,mew=.85,ls="None",zorder=4)
    changed=imax!=jmax
    ax.set_xlim(-.20,4.20);ax.set_ylim(120,365)
    ax.set_xticks(x,ticks);ax.set_yticks([150,250,350])
    ax.tick_params(axis="x",pad=4)
    if col==0:
        ax.set_ylabel("CO$_2$ ceiling\n(kg per Mg fraction)",labelpad=5)
    else:
        ax.tick_params(labelleft=False)
    if row==1:
        ax.set_xlabel("Particle size (mm)",labelpad=6)
    fig_text(fig,left-.044,bottom+.332,"abcde"[index],fontsize=10.,fontweight="bold")
    fig_text(fig,left,bottom+.332,plant+("*" if plant=="PC" else ""),fontsize=9.5,fontweight="bold")
    pick=lambda r:f"{float(r['fraction_lower_mm']):g}–{float(r['fraction_upper_mm']):g}"
    robust=bool(corrected[jmax]-float(rows[jmax]["XRD_display_rounding_Ceiling_half_width_kg_per_Mg"])>
                corrected[imax]+float(rows[imax]["XRD_display_rounding_Ceiling_half_width_kg_per_Mg"])) if changed else None
    ranking.append({"plant":plant,"oxide_only_highest_fraction_mm":pick(rows[imax]),
                    "carbonate_corrected_highest_fraction_mm":pick(rows[jmax]),
                    "ceiling_selection_difference_kgCO2_per_Mg_fraction":float(corrected[jmax]-corrected[imax]),
                    "ranking_changed":changed,"change_survives_display_rounding":robust,
                    "source_csv":FILES["italian_samples"].relative_to(ROOT).as_posix()})
for y,label,color,marker,fill in [(.438,"CaO only",GRAY,"o","white"),
                                  (.374,"Carbonate corrected",BLUE,"s",BLUE)]:
    fig_line(fig,[.735,.775],[y,y],color=color,lw=.8)
    fig_line(fig,[.755],[y],marker=marker,ms=3.6,mfc=fill,mec=color,ls="None")
    fig_text(fig,.788,y,label)
fig_line(fig,[.755],[.31],marker="o",ms=7.1,mfc="none",mec=ORANGE,mew=.85,ls="None")
fig_text(fig,.788,.31,"Within-plant maximum")
fig_text(fig,.715,.223,"Priorities change: 3/5")
fig_text(fig,.715,.153,"*PC: rounding-sensitive")
fig_text(fig,.715,.091,"TO, FC: rounding-stable")
save(fig,"figure2_italian_carbonate_priority","Five plant panels, all 25 records; outlined maxima and a separate legend/rounding note.")
shutil.copyfile(FILES["italian_samples"],DATA/"figure2_italian_samples.csv")
write_csv("figure2_within_plant_ranking.csv",ranking)

# Figure 3: candidate yield is graphical; the source table keeps the numerical
# performance/release data. The matrix uses separate text and status columns.
spanish=read(FILES["spanish_samples"])
fractions=[r for r in spanish if r["fraction"]!="Entire"]
strength_share=100*sum(float(r["approximate_feed_mass_fraction"]) for r in fractions if r["strength_75_percent_screen_pass"]=="True")
mo_share=100*sum(float(r["approximate_feed_mass_fraction"]) for r in fractions if r["mortar_Mo_comparative_pass"]=="True")
joint_share=100*sum(float(r["approximate_feed_mass_fraction"]) for r in fractions if r["strength_and_Mo_comparative_pass"]=="True")
assert [round(strength_share),round(mo_share),round(joint_share)]==[54,46,0]
fig=plt.figure(figsize=(18/2.54,11.3/2.54))
panel_heading(fig,"a","Candidate feed shares",.038,.957)
ax=fig.add_axes([.205,.675,.435,.20])
for y,value in [(1,strength_share),(0,mo_share)]:
    ax.add_patch(Rectangle((0,y-.115),value,.23,facecolor=BLUE,edgecolor="none"))
    ax.text(value+5,y,f"≈{value:.0f}%",ha="left",va="center",color=BLUE,fontsize=9.2)
ax.set_xlim(0,100);ax.set_ylim(-.50,1.50)
ax.set_xticks([0,50,100]);ax.set_yticks([1,0],["Strength","Mo"])
ax.tick_params(axis="y",length=0,pad=9);ax.spines["left"].set_visible(False)
ax.set_xlabel("Approximate feed share (%)",labelpad=5)
fig_text(fig,.81,.875,"Joint",ha="center",fontsize=9.5)
fig_text(fig,.81,.790,"0%",ha="center",fontsize=21.,fontweight="bold")
fig_text(fig,.81,.712,"candidate share",ha="center")
panel_heading(fig,"b","Same-fraction intersection",.038,.523)
fig_line(fig,[.69],[.523],marker="o",ms=4.8,mfc=BLUE,mec=BLUE,ls="None")
fig_text(fig,.706,.523,"Pass")
fig_line(fig,[.825],[.523],marker="x",ms=4.8,color=ORANGE,mew=1.,ls="None")
fig_text(fig,.842,.523,"Fail")
for x,title in [(.085,"Fraction (mm)"),(.345,"Feed share"),(.54,"Strength"),(.70,"Mo"),(.86,"Both")]:
    fig_text(fig,x,.453,title,ha="left" if x==.085 else "center",fontsize=9.2)
fig_text(fig,.54,.417,"75% SAI",ha="center",fontsize=9.2)
fig_text(fig,.70,.417,"≤0.5 mg/kg",ha="center",fontsize=9.2)
fig_line(fig,[.085,.945],[.386,.386],color=GRAY,lw=.5)
status_rows=[]
for row,y in zip(spanish,[.345,.285,.225,.165,.105,.027]):
    whole=row["fraction"]=="Entire"
    label="Whole mixture" if whole else row["fraction"].replace("-","–")
    share="—" if whole else f"≈{100*float(row['approximate_feed_mass_fraction']):.0f}%"
    fig_text(fig,.085,y,label)
    fig_text(fig,.345,y,share,ha="center")
    passes=[row[key]=="True" for key in ["strength_75_percent_screen_pass","mortar_Mo_comparative_pass","strength_and_Mo_comparative_pass"]]
    for x,passed in zip([.54,.70,.86],passes):
        if passed:
            fig_line(fig,[x],[y],marker="o",ms=4.8,mfc=BLUE,mec=BLUE,ls="None")
        else:
            fig_line(fig,[x],[y],marker="x",ms=4.8,color=ORANGE,mew=1.,ls="None")
    status_rows.append({"fraction":label,"approximate_feed_mass_share_percent":"" if whole else 100*float(row["approximate_feed_mass_fraction"]),
                        "strength_pass":passes[0],"Mo_pass":passes[1],"joint_pass":passes[2],
                        "whole_mixture_separate_formulation":whole})
fig_line(fig,[.085,.945],[.064,.064],color=GRAY,lw=.5)
save(fig,"figure3_spanish_joint_screen","Independent candidate shares and a sparse point/cross benchmark matrix; no invented material flow.")
shutil.copyfile(FILES["spanish_samples"],DATA/"figure3_spanish_samples.csv")
write_csv("figure3_status_matrix.csv",status_rows)
write_csv("figure3_candidate_shares.csv",[{"strength_candidate_percent_approximate":strength_share,
          "Mo_candidate_percent_approximate":mo_share,"joint_candidate_percent":joint_share}])

# Figure 4: small one-scenario horizontal effect plot; values above the endpoints.
swedish=read(FILES["swedish_grid"])
selected=[r for r in swedish if int(r["case"])==2 and r["road_type"]=="single"
          and r["transport_setting"]=="HVO10_source_base" and float(r["p"])==10 and float(r["q"])==.5]
assert len(selected)==1
record=selected[0]
values=[float(record["all_batch_net_if_Delta_zero"]),float(record["eligible_only_net_if_Delta_zero"])]
assert [round(v,2) for v in values]==[3.85,-1.15]
fig=plt.figure(figsize=(9/2.54,6.8/2.54))
fig_text(fig,.09,.951,"Project 2 · HVO 10",fontsize=9.5)
fig_text(fig,.09,.873,"q = 0.5; p = 10; Δ = 0",fontsize=9.2)
ax=fig.add_axes([.34,.255,.62,.472])
for y,value,color in zip([1,0],values,[ORANGE,BLUE]):
    ax.plot([0,value],[y,y],color=color,lw=1.)
    ax.plot([value],[y],marker="o",ms=4.5,color=color,ls="None")
    ax.text(value,y+.225,f"{value:+.2f}",ha="center",va="bottom",fontsize=9.5,color=color)
ax.axvline(0,color=GRAY,lw=.5,zorder=0)
ax.set_xlim(-2.2,5.2);ax.set_ylim(-.55,1.65)
ax.set_xticks([-2,0,2,4]);ax.set_yticks([1,0],["Whole batch","Eligible portion"])
ax.tick_params(axis="y",length=0,pad=7);ax.spines["left"].set_visible(False)
ax.set_xlabel("Net climate change\n(kg CO$_2$-eq per Mg candidate)",labelpad=5)
save(fig,"figure4_swedish_processing_example","One explicitly hypothetical Swedish conditioning scenario, with sign reversal at two allocation extents.")
record_out=dict(record)
record_out.update({"source_csv":FILES["swedish_grid"].relative_to(ROOT).as_posix(),"source_row_1_based_after_header":swedish.index(record)+1,
                   "hypothetical_extra_burden":True,"eligible_only_requires_prior_independent_eligibility":True})
write_csv("figure4_swedish_selected_scenario.csv",[record_out])

# Graphical abstract: independent evidence columns, exact WBV 8 x 3 cm canvas.
# No arrow suggests any cross-country transferable material or treatment chain.
fig=plt.figure(figsize=(8/2.54,3/2.54))
for x,country,value,detail,last in [(.171,"Germany","58.2%","clinker-stream mass","≈70% direct credit"),
                                  (.5,"Italy","3/5","priorities changed","2 rounding-stable"),
                                  (.829,"Spain","0%","joint candidates","≈54% SAI · ≈46% Mo")]:
    fig_text(fig,x,.865,country,ha="center",fontsize=6.8,fontweight="bold")
    fig_text(fig,x,.625,value,ha="center",fontsize=10.,fontweight="bold",color=BLUE)
    fig_text(fig,x,.423,detail,ha="center",fontsize=6.15)
    fig_text(fig,x,.265,last,ha="center",fontsize=6.15)
fig_line(fig,[.337,.337],[.215,.938],color=LIGHT,lw=.5)
fig_line(fig,[.663,.663],[.215,.938],color=LIGHT,lw=.5)
fig_text(fig,.5,.077,"Independent cases; source benchmarks",ha="center",fontsize=6.15)
save(fig,"graphical_abstract","Exact 8 x 3 cm independent three-country evidence summary, without transfer arrows.")

captions="""# Suggested v113 captions (presentation updated; numerical meaning unchanged)

Figure 1. Fraction mass, direct calcination credit and accepted-mass climate margins in the German source scenarios. (a) Paired points compare fine-fraction shares of the 407.93 kg clinker-directed mineral stream and source-reconciled direct avoided-calcination credit in three source scenarios. Medium-fraction shares are the corresponding complements; direct credit is not total life-cycle credit. (b–d) Fine-first and medium-first acceptance bound climate margin M for the laboratory, high-ambition and worst-case scenarios, respectively, assuming fixed stream compositions and equivalent clinker function. Pale shading identifies accepted masses compatible with either climate sign when the signed adjustment to other exchanges is zero (Δ = 0). Endpoints are break-even. Additional changed exchanges can exceed a positive margin. These are deterministic accounting bounds, not confidence intervals.

Figure 2. CaO-only and carbonate-corrected CO₂ ceilings for all 25 linked Italian plant–fraction records. Each ceiling refers to one Mg of isolated dry fraction and assumes displacement of limestone-derived calcium; identified calcite and vaterite supply the correction. Outlined markers identify within-plant maxima. Highest-ceiling fractions change in PC, TO and FC. The PC change does not survive display-rounding sensitivity for quantified carbonate phases; TO and FC changes do. This check is not analytical uncertainty. Missing/unquantified phases and untested raw-meal functionality remain unresolved; ceilings are not verified clinker substitution credits or complete LCA results.

Figure 3. Joint strength and molybdenum benchmark screens for the Spanish composite. (a) Approximate feed shares satisfying separate strength and Mo benchmarks, and their empty intersection. (b) Filled dots denote pass and crosses denote fail for the same-fraction benchmark comparisons. Strength uses the reported 28-day 75% SAI screen. Mo uses the source inert-landfill comparator of ≤0.5 mg/kg for corresponding crushed mortars containing 25 wt.% ash in the binder, tested at L/S 10 L/kg. The whole-mixture formulation is separate and contributes no additional fraction share. Neither benchmark set establishes construction-product approval. Source measurements, including about 70% or >75% strength statements, are retained in Table 4; no exact value is imputed.

Figure 4. Illustrative processing allocation for Swedish Project 2, single-road geometry and source HVO 10 setting. The displayed scenario uses eligible diversion q = 0.5, hypothetical additional processing burden p = 10 kg CO₂-eq per Mg conditioned and no adjustment to other exchanges (Δ = 0). Impacts are normalized per Mg candidate material, including its ineligible portion. Whole-batch processing gives +3.85 kg CO₂-eq/Mg; processing only the eligible half gives −1.15. The latter requires prior, independently established eligibility and is unavailable when processing itself establishes eligibility. The 5.00 kg difference is conditional, not observed treatment savings or an inventoried washing result. Source reference functions are retained.

Graphical abstract. Three independent case results illustrate the need to preserve fraction yield, carbonate-dependent substitution potential and same-material joint performance/release information. German and Italian numerical coefficients are not transferred to the Spanish material. Spanish candidate shares are approximate; the screens are source benchmarks, not construction approval.
"""
(DATA/"figure_captions.md").write_text(captions,encoding="utf-8")
manifest={"script":"src/make_wbv_figures_v113.py","script_sha256":sha(Path(__file__)),
          "runtime":{"python_executable_name":Path(sys.executable).name,"python_version":sys.version,
                     "matplotlib_version":matplotlib.__version__,"matplotlib_library":"matplotlib",
                     "numpy_version":np.__version__,"numpy_library":"numpy",
                     "matplotlib_configuration_and_font_cache":MPL_CACHE.relative_to(ROOT).as_posix()},
          "source_files":[{"key":key,"path":path.relative_to(ROOT).as_posix(),"sha256":sha(path)} for key,path in FILES.items()],
          "style":{"actually_loaded_in_order":[p.relative_to(ROOT).as_posix() for p in STYLE_FILES],
                   "style_sha256":[sha(p) for p in STYLE_FILES],"license":(STYLES/"LICENSE").relative_to(ROOT).as_posix(),
                   "overrides":OVERRIDES,"font_file_name":ARIAL.name,
                   "description":"Original SciencePlots science + no-latex + nature; explicit task/accessibility overrides. Nature-inspired visual presentation for a WBV submission, not a Nature submission claim."},
          "figures":GEOMETRY,
          "verification":{"source_values_from_existing_outputs":True,"models_changed":False,
                          "invented_uncertainty":False,"all_deterministic_collision_tests_passed":True,
                          "detector_positive_controls":POSITIVE_CONTROLS,
                          "missing_glyph_warnings_promoted_to_errors":True,
                          "all_vectors_have_no_embedded_images":True,"visual_inspection":"pending 300 dpi print previews"}}
(DATA/"figure_manifest.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
print(json.dumps({"figures":str(OUT),"figure_data":str(DATA),"artifact_count":len(GEOMETRY),
                  "collision_audit":"PASS","vector_audit":"PASS","visual_inspection":"pending"},indent=2))
