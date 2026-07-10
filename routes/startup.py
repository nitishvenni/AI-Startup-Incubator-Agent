"""
routes/startup.py - Create, view, edit, delete, export startup project routes.
"""

import logging
import traceback
from flask import (
    Blueprint, render_template, request,
    redirect, url_for, flash, current_app,
    send_file, abort,
)
import io
from models.startup import (
    create_startup, get_startup_by_id, delete_startup,
    update_startup_status, update_startup,
)
from models.report import create_report, get_report_by_project
from models.incubation_report import (
    save_incubation_report, get_incubation_report_by_project,
)
from models.activity import log_activity
from services.watsonx_service import analyze_startup
from utils.helpers import format_datetime, score_label, score_color, industry_icon
from utils.validators import validate_startup_form
from utils.constants import INDUSTRIES, BUDGETS, COUNTRIES

logger = logging.getLogger(__name__)
startup_bp = Blueprint("startup", __name__)
print("[TRACE] MODULE LOAD routes.startup __file__ =", __file__)
print("[TRACE] routes.startup imported analyze_startup =", analyze_startup)
print("[TRACE] routes.startup imported analyze_startup.__module__ =", getattr(analyze_startup, "__module__", None))
print("[TRACE] routes.startup imported analyze_startup.__globals__['__file__'] =", analyze_startup.__globals__.get("__file__"))


# ------------------------------------------------------------------ #
# Create                                                               #
# ------------------------------------------------------------------ #

@startup_bp.route("/create", methods=["GET", "POST"])
def create():
    """Render the create-startup form and handle submission."""
    if request.method == "POST":
        data, errors = validate_startup_form(request.form)
        if errors:
            for err in errors:
                flash(err, "danger")
            return render_template(
                "create_startup.html",
                industries=INDUSTRIES, budgets=BUDGETS, countries=COUNTRIES,
                form_data=request.form,
            )

        app = current_app._get_current_object()
        project_id = create_startup(app, data)
        log_activity(app, "startup_created",
                     f"New startup '{data['startup_name']}' created.",
                     project_id=project_id)
        flash(
            f"Startup '{data['startup_name']}' created! "
            "Use the workspace to generate AI reports.",
            "success",
        )
        return redirect(url_for("startup.detail", project_id=project_id))

    return render_template(
        "create_startup.html",
        industries=INDUSTRIES, budgets=BUDGETS, countries=COUNTRIES,
        form_data={},
    )


# ------------------------------------------------------------------ #
# Detail / Workspace                                                   #
# ------------------------------------------------------------------ #

@startup_bp.route("/<int:project_id>")
def detail(project_id: int):
    """Detail / workspace view for a single startup project."""
    print("[TRACE] ENTER routes.startup.detail(project_id)")
    print("[TRACE] detail project_id =", repr(project_id))
    app = current_app._get_current_object()
    startup = get_startup_by_id(app, project_id)
    if not startup:
        flash("Startup project not found.", "danger")
        return redirect(url_for("main.history"))

    report = get_report_by_project(app, project_id)
    incubation_report = get_incubation_report_by_project(app, project_id)

    startup["icon"] = industry_icon(startup["industry"])
    startup["created_at_fmt"] = format_datetime(startup["created_at"])

    if report:
        for dim in ("viability", "market", "innovation", "execution"):
            key = f"{dim}_score"
            report[f"{dim}_label"] = score_label(report[key])
            report[f"{dim}_color"] = score_color(report[key])

    if incubation_report:
        incubation_report["created_at_fmt"] = format_datetime(
            incubation_report["created_at"]
        )
        print("[TRACE] detail incubation_report id =", repr(incubation_report.get("id")))
        print("[TRACE] detail incubation_report validation_score =", repr(incubation_report.get("validation_score")))
        print("[TRACE] detail incubation_report sections keys =", sorted((incubation_report.get("sections") or {}).keys()))
    else:
        print("[TRACE] detail incubation_report = None")

    print("[TRACE] RENDER detail.html startup id =", repr(startup.get("id")))
    return render_template(
        "detail.html",
        startup=startup,
        report=report,
        incubation_report=incubation_report,
    )


# ------------------------------------------------------------------ #
# Edit                                                                 #
# ------------------------------------------------------------------ #

@startup_bp.route("/<int:project_id>/edit", methods=["GET", "POST"])
def edit(project_id: int):
    """Edit an existing startup project."""
    app = current_app._get_current_object()
    startup = get_startup_by_id(app, project_id)
    if not startup:
        flash("Startup project not found.", "danger")
        return redirect(url_for("main.history"))

    if request.method == "POST":
        data, errors = validate_startup_form(request.form)
        if errors:
            for err in errors:
                flash(err, "danger")
            return render_template(
                "edit_startup.html",
                startup=startup,
                industries=INDUSTRIES, budgets=BUDGETS, countries=COUNTRIES,
                form_data=request.form,
            )

        update_startup(app, project_id, data)
        log_activity(app, "startup_edited",
                     f"Startup '{data['startup_name']}' updated.",
                     project_id=project_id)
        flash("Startup updated successfully!", "success")
        return redirect(url_for("startup.detail", project_id=project_id))

    return render_template(
        "edit_startup.html",
        startup=startup,
        industries=INDUSTRIES, budgets=BUDGETS, countries=COUNTRIES,
        form_data=startup,
    )


# ------------------------------------------------------------------ #
# Delete                                                               #
# ------------------------------------------------------------------ #

@startup_bp.route("/<int:project_id>/delete", methods=["POST"])
def delete(project_id: int):
    """Hard-delete a project and redirect to history."""
    app = current_app._get_current_object()
    startup = get_startup_by_id(app, project_id)
    if startup:
        name = startup["startup_name"]
        delete_startup(app, project_id)
        log_activity(app, "startup_deleted",
                     f"Startup '{name}' deleted.",
                     project_id=None)
        flash(f"'{name}' has been deleted.", "info")
    return redirect(url_for("main.history"))


# ------------------------------------------------------------------ #
# AI Report Generation                                                 #
# ------------------------------------------------------------------ #

@startup_bp.route("/<int:project_id>/generate-analysis", methods=["POST"])
def generate_analysis(project_id: int):
    """Generate (or regenerate) the AI Startup Analysis from stored startup data."""
    print("[TRACE] ENTER routes.startup.generate_analysis(project_id)")
    print("[TRACE] generate_analysis project_id =", repr(project_id))
    print("[TRACE] generate_analysis request.method =", repr(request.method))
    print("[TRACE] generate_analysis request.path =", repr(request.path))

    app = current_app._get_current_object()
    print("[TRACE] generate_analysis current_app =", repr(app))
    print("[TRACE] generate_analysis app.config IBM_MODEL =", repr(app.config.get("IBM_MODEL")))
    print("[TRACE] generate_analysis app.config IBM_URL =", repr(app.config.get("IBM_URL")))
    print("[TRACE] generate_analysis app.config IBM_PROJECT_ID =", repr(app.config.get("IBM_PROJECT_ID")))
    print("[TRACE] generate_analysis app.config IBM_API_KEY length =", len(app.config.get("IBM_API_KEY") or ""))

    startup = get_startup_by_id(app, project_id)
    print("[TRACE] generate_analysis startup =", repr(startup))
    if not startup:
        flash("Project not found.", "danger")
        return redirect(url_for("main.history"))

    try:
        print("[TRACE] CALL services.watsonx_service.analyze_startup(app, startup)")
        analysis = analyze_startup(app, startup)
        print("[TRACE] RETURN analyze_startup analysis =", repr(analysis))
        create_report(app, {
            "project_id":       project_id,
            "report_type":      "full_analysis",
            "content":          analysis["content"],
            "viability_score":  analysis["viability_score"],
            "market_score":     analysis["market_score"],
            "innovation_score": analysis["innovation_score"],
            "execution_score":  analysis["execution_score"],
        })
        update_startup_status(app, project_id, "analyzed")
        log_activity(app, "report_generated",
                     f"AI analysis completed for '{startup['startup_name']}'.",
                     project_id=project_id,
                     meta={"viability": analysis["viability_score"]})
        flash("AI Startup Analysis generated successfully!", "success")
    except Exception:
        print("[TRACE] EXCEPTION in routes.startup.generate_analysis(project_id)")
        traceback.print_exc()
        raise

    print("[TRACE] EXIT routes.startup.generate_analysis(project_id)")
    return redirect(url_for("startup.detail", project_id=project_id))


@startup_bp.route("/<int:project_id>/reanalyze", methods=["POST"])
def reanalyze(project_id: int):
    """Backward-compat alias — delegates to generate_analysis."""
    return generate_analysis(project_id)


@startup_bp.route("/<int:project_id>/generate-incubation", methods=["POST"])
def generate_incubation(project_id: int):
    """Generate (or regenerate) the AI Incubation Report from stored startup data."""
    from services.mentor_ai_service import generate_incubation_report
    print("[TRACE] ENTER routes.startup.generate_incubation(project_id)")
    print("[TRACE] routes.startup __file__ =", __file__)
    print("[TRACE] generate_incubation imported generate_incubation_report =", generate_incubation_report)
    print("[TRACE] generate_incubation_report.__globals__['__file__'] =", generate_incubation_report.__globals__.get("__file__"))
    print("[TRACE] generate_incubation project_id =", repr(project_id))
    app = current_app._get_current_object()
    startup = get_startup_by_id(app, project_id)
    print("[TRACE] generate_incubation startup =", repr(startup))
    if not startup:
        flash("Project not found.", "danger")
        return redirect(url_for("main.history"))

    try:
        print("[TRACE] CALL services.mentor_ai_service.generate_incubation_report(app, startup)")
        result = generate_incubation_report(app, startup)
        print("[TRACE] RETURN generate_incubation_report result =", repr(result))
        save_payload = {
            "project_id":       project_id,
            **{k: startup[k] for k in (
                "startup_name", "founder_name", "industry", "country",
                "budget", "target_audience", "business_goal", "idea_description",
            )},
            "validation_score": result["validation_score"],
            "sections":         result["sections"],
        }
        print("[TRACE] CALL save_incubation_report payload =", repr(save_payload))
        report_id = save_incubation_report(app, save_payload)
        print("[TRACE] RETURN save_incubation_report report_id =", repr(report_id))
        log_activity(app, "mentor_report_generated",
                     f"Incubation report generated for '{startup['startup_name']}'.",
                     project_id=project_id)
        flash("AI Incubation Report generated successfully!", "success")
    except Exception as exc:
        import traceback
        print("[TRACE] EXCEPTION in routes.startup.generate_incubation(project_id)")
        traceback.print_exc()
        logger.error("Incubation report failed for project %d: %s", project_id, exc)
        flash(f"Incubation report failed: {exc}", "warning")

    print("[TRACE] EXIT routes.startup.generate_incubation(project_id)")
    return redirect(url_for("startup.detail", project_id=project_id))


# ------------------------------------------------------------------ #
# Export routes                                                        #
# ------------------------------------------------------------------ #

@startup_bp.route("/<int:project_id>/export/pdf")
def export_pdf(project_id: int):
    """Export the startup analysis as a PDF."""
    app = current_app._get_current_object()
    startup = get_startup_by_id(app, project_id)
    if not startup:
        abort(404)
    report = get_report_by_project(app, project_id)

    try:
        from utils.export import report_to_pdf
        pdf_bytes = report_to_pdf(startup, report)
    except RuntimeError as exc:
        flash(str(exc), "danger")
        return redirect(url_for("startup.detail", project_id=project_id))

    log_activity(app, "export_pdf",
                 f"PDF exported for '{startup['startup_name']}'.",
                 project_id=project_id)
    filename = f"{startup['startup_name'].replace(' ', '_')}_analysis.pdf"
    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=filename,
    )


@startup_bp.route("/<int:project_id>/export/docx")
def export_docx(project_id: int):
    """Export the startup analysis as a DOCX."""
    app = current_app._get_current_object()
    startup = get_startup_by_id(app, project_id)
    if not startup:
        abort(404)
    report = get_report_by_project(app, project_id)

    try:
        from utils.export import report_to_docx
        docx_bytes = report_to_docx(startup, report)
    except RuntimeError as exc:
        flash(str(exc), "danger")
        return redirect(url_for("startup.detail", project_id=project_id))

    log_activity(app, "export_docx",
                 f"DOCX exported for '{startup['startup_name']}'.",
                 project_id=project_id)
    filename = f"{startup['startup_name'].replace(' ', '_')}_analysis.docx"
    return send_file(
        io.BytesIO(docx_bytes),
        mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        as_attachment=True,
        download_name=filename,
    )
