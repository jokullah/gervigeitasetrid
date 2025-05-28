from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse

@csrf_exempt
def hide_translation_notice(request):
    if request.method == "POST":
        request.session["hide_translation_notice"] = True
        return JsonResponse({"status": "ok"})
    return JsonResponse({"status": "ignored"})
