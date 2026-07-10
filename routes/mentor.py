"""
routes/mentor.py - AI Startup Mentor incubation report routes.
"""

import io
import logging
from flask import (
    Blueprint, render_template, request, redirect,
    url_for, flash, current_app, send_file, abort,
)
from services.mentor_ai_service import generate_incubation_report
from models.incubation_report import (
    save_incubation_report, get_incubation_report_by_id,
    get_all_incubation_reports, delete_incubation_report,
)
from models.activity import log_activity
from utils.helpers import format_datetime, industry_icon
from utils.constants import INDUSTRIES, BUDGETS, COUNTRIES

logger = logging.getLogger(__name__)
mentor_bp = Blueprint("mentor", __name__)
print("[TRACE] MODULE LOAD routes.mentor __file__ =", __file__)
print("[TRACE] routes.mentor imported generate_incubation_report =", generate_incubation_report)
print("[TRACE] routes.mentor generate_incubation_report.__globals__['__file__'] =", generate_incubation_report.__globals__.get("__file__"))


@mentor_bp.route("/")
def index():
    """Show the mentor idea submission form."""
    return render_template(
        "mentor_form.html",
        industries=INDUSTRIES, budgets=BUDGETS, countries=COUNTRIES,
        form_data={},
    )


@mentor_bp.route("/generate", methods=["POST"])
def generate():
    """Generate a full incubation report and save it."""
    print("[TRACE] ENTER routes.mentor.generate()")
    print("[TRACE] routes.mentor __file__ =", __file__)
    from utils.validators import validate_startup_form
    data, errors = validate_startup_form(request.form)
    print("[TRACE] mentor.generate form data =", repr(data))
    print("[TRACE] mentor.generate validation errors =", repr(errors))
    if errors:
        for err in errors:
            flash(err, "danger")
        return render_template(
            "mentor_form.html",
            industries=INDUSTRIES, budgets=BUDGETS, countries=COUNTRIES,
            form_data=request.form,
        )

    app = current_app._get_current_object()

    try:
        print("[TRACE] CALL services.mentor_ai_service.generate_incubation_report(app, data)")
        result = generate_incubation_report(app, data)
        print("[TRACE] RETURN generate_incubation_report result =", repr(result))
        save_payload = {
            **data,
            "validation_score": result["validation_score"],
            "sections":         result["sections"],
        }
        print("[TRACE] CALL save_incubation_report payload =", repr(save_payload))
        report_id = save_incubation_report(app, save_payload)
        print("[TRACE] RETURN save_incubation_report report_id =", repr(report_id))
        log_activity(app, "mentor_report_generated",
                     f"Mentor incubation report generated for '{data['startup_name']}'.")
        flash("Your incubation report has been generated successfully!", "success")
        return redirect(url_for("mentor.view_report", report_id=report_id))
    except Exception as exc:
        import traceback
        print("[TRACE] EXCEPTION in routes.mentor.generate()")
        traceback.print_exc()
        logger.error("Incubation report generation failed: %s", exc)
        flash(f"Report generation failed: {exc}", "warning")
        return render_template(
            "mentor_form.html",
            industries=INDUSTRIES, budgets=BUDGETS, countries=COUNTRIES,
            form_data=request.form,
        )


@mentor_bp.route("/report/<int:report_id>")
def view_report(report_id: int):
    """Display a saved incubation report."""
    print("[TRACE] ENTER routes.mentor.view_report(report_id)")
    print("[TRACE] view_report report_id =", repr(report_id))
    app = current_app._get_current_object()
    report = get_incubation_report_by_id(app, report_id)
    print("[TRACE] view_report db report =", repr(report))
    if not report:
        flash("Report not found.", "danger")
        return redirect(url_for("mentor.history"))

    report["icon"] = industry_icon(report["industry"])
    report["created_at_fmt"] = format_datetime(report["created_at"])
    print("[TRACE] RENDER mentor_report.html report.validation_score =", repr(report.get("validation_score")))
    print("[TRACE] RENDER mentor_report.html report.sections keys =", sorted((report.get("sections") or {}).keys()))
    return render_template("mentor_report.html", report=report)


@mentor_bp.route("/history")
def history():
    """List all saved incubation reports."""
    app = current_app._get_current_object()
    reports = get_all_incubation_reports(app)
    for r in reports:
        r["icon"] = industry_icon(r["industry"])
        r["created_at_fmt"] = format_datetime(r["created_at"])
    return render_template("mentor_history.html", reports=reports)


@mentor_bp.route("/report/<int:report_id>/delete", methods=["POST"])
def delete_report(report_id: int):
    """Delete a report and redirect to mentor history."""
    app = current_app._get_current_object()
    report = get_incubation_report_by_id(app, report_id)
    if report:
        delete_incubation_report(app, report_id)
        log_activity(app, "mentor_report_deleted",
                     f"Mentor report for '{report['startup_name']}' deleted.")
        flash(f"Report for '{report['startup_name']}' has been deleted.", "info")
    return redirect(url_for("mentor.history"))


@mentor_bp.route("/report/<int:report_id>/export/pdf")
def export_pdf(report_id: int):
    """Export a mentor incubation report as PDF."""
    app = current_app._get_current_object()
    report = get_incubation_report_by_id(app, report_id)
    if not report:
        abort(404)
    try:
        from utils.export import incubation_report_to_pdf
        pdf_bytes = incubation_report_to_pdf(report)
    except RuntimeError as exc:
        flash(str(exc), "danger")
        return redirect(url_for("mentor.view_report", report_id=report_id))

    log_activity(app, "export_pdf",
                 f"PDF exported for mentor report '{report['startup_name']}'.")
    filename = f"{report['startup_name'].replace(' ', '_')}_incubation_report.pdf"
    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=filename,
    )


@mentor_bp.route("/report/<int:report_id>/export/docx")
def export_docx(report_id: int):
    """Export a mentor incubation report as DOCX."""
    app = current_app._get_current_object()
    report = get_incubation_report_by_id(app, report_id)
    if not report:
        abort(404)
    try:
        from utils.export import incubation_report_to_docx
        docx_bytes = incubation_report_to_docx(report)
    except RuntimeError as exc:
        flash(str(exc), "danger")
        return redirect(url_for("mentor.view_report", report_id=report_id))

    log_activity(app, "export_docx",
                 f"DOCX exported for mentor report '{report['startup_name']}'.")
    filename = f"{report['startup_name'].replace(' ', '_')}_incubation_report.docx"
    return send_file(
        io.BytesIO(docx_bytes),
        mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        as_attachment=True,
        download_name=filename,
    )
