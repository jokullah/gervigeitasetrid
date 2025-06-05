document.addEventListener("DOMContentLoaded", () => {
  const dismissBtn = document.getElementById("dismiss-translation-alert");
  if (dismissBtn) {
    dismissBtn.addEventListener("click", () => {
      fetch("/admin/hide-translation-notice/", {
        method: "POST",
        headers: {
          "X-CSRFToken": getCookie("csrftoken"),
          "Content-Type": "application/json"
        }
      }).then(() => {
        dismissBtn.closest(".translation-alert").remove();
      });
    });
  }
});

function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== "") {
    for (const cookie of document.cookie.split(";")) {
      const trimmed = cookie.trim();
      if (trimmed.startsWith(name + "=")) {
        cookieValue = decodeURIComponent(trimmed.slice(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}
