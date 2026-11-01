from django.http import HttpResponse, JsonResponse

from .rag import answer


def index(request):
    return HttpResponse("Elden Ring build assistant.")


def ask(request):
    query = request.GET.get("q", "")
    if not query:
        return JsonResponse({"error": "Provide a question with /?q=..."}, status=400)
    return JsonResponse({"question": query, "answer": answer(query)})