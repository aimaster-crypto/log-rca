from flask import Blueprint, render_template, request, jsonify
from .services import db_ingest, rca as rca_service

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    return render_template("index.html")

@bp.route('/api/logs', methods=['GET'])
def get_logs():
    cid = request.args.get('correlation_id')
    if not cid:
        return jsonify({"error": "correlation_id required"}), 400
    
    logs = db_ingest.fetch_logs_by_correlation(cid)
    return jsonify({"logs": logs, "count": len(logs)})

@bp.route('/analyze', methods=['POST'])
def analyze():
    data = request.get_json()
    if not data or 'correlation_id' not in data:
        return jsonify({"error": "correlation_id required"}), 400
    
    cid = data['correlation_id']
    try:
        result = rca_service.analyze_correlation(cid)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.post("/ingest")
def ingest():
    # Trigger code scan and vector index build
    return jsonify({"status": "ok"})

@bp.post("/ingest/path")
def ingest_path():
    data = request.get_json(silent=True) or request.form
    java_path = (data.get("java_path") or "").strip()
    if not java_path:
        return jsonify({"error": "java_path is required"}), 400
    count = code_scan.scan_and_index(java_path)
    return jsonify({"count": count, "path": java_path, "documents_indexed": count})
