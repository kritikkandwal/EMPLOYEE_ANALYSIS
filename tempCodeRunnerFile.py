@app.route('/api/update-productivity', methods=['POST'])
# @login_required
# def api_update_productivity():
#     data = request.json
#     date = data.get("date")
#     completed = data.get("completed", 0)
#     total = data.get("total", 0)
#     score = data.get("score", 0)

#     productivity_forecaster.update_today(
#     current_user.id,
#     today_score=score,
#     completed=completed,
#     total=total
#     )


#     return jsonify({"status": "success", "message": "Productivity updated"})