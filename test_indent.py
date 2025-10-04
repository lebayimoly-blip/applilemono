def add_incident(plate):
    description = "Test"
    photo_filename = None

    date = "2025-09-24"
    time = "04:00:00"
    agent_name = "Moly"

    print("✅ Incident prêt à être enregistré :", plate, description, date, time, agent_name)

    return f"/vehicle/{plate}"
