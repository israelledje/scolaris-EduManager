// gestion_classes.js
// JS personnalisé pour l'intégration htmx des classes et emplois du temps

document.addEventListener('DOMContentLoaded', function () {
    // Gestion de l'ouverture/fermeture du modal
    window.openClassModal = function () {
        document.getElementById('modal').classList.remove('hidden');
    };
    window.closeModal = function () {
        document.getElementById('modal').classList.add('hidden');
        document.getElementById('modal-content').innerHTML = '';
    };

    // Fermer le modal en cliquant sur l'arrière-plan
    document.getElementById('modal').addEventListener('click', function (e) {
        if (e.target === this) {
            window.closeModal();
        }
    });

    // Notification simple
    window.showNotification = function (message, type = 'success') {
        let notif = document.createElement('div');
        notif.className = `fixed top-5 right-5 z-50 px-4 py-2 rounded shadow-lg text-white ${type === 'success' ? 'bg-green-600' : 'bg-red-600'}`;
        notif.innerText = message;
        document.body.appendChild(notif);
        setTimeout(() => notif.remove(), 2500);
    };

    // htmx events pour feedback et rafraîchissement
    document.body.addEventListener('htmx:afterSwap', function (evt) {
        // Si on vient de créer ou modifier une classe/emploi du temps
        if (evt.detail.target && evt.detail.target.id === 'modal-content') {
            // Si le fragment contient une ligne de table, on l'insère/remplace
            let row = evt.detail.target.querySelector('tr');
            if (row) {
                let table = document.querySelector('table tbody');
                if (row.id.startsWith('schoolclass-')) {
                    let oldRow = document.getElementById(row.id);
                    if (oldRow) {
                        oldRow.replaceWith(row);
                        window.showNotification('Classe modifiée avec succès');
                    } else {
                        table.prepend(row);
                        window.showNotification('Classe créée avec succès');
                    }
                } else if (row.id.startsWith('timetable-')) {
                    let oldRow = document.getElementById(row.id);
                    if (oldRow) {
                        oldRow.replaceWith(row);
                        window.showNotification('Emploi du temps modifié avec succès');
                    } else {
                        table.prepend(row);
                        window.showNotification('Emploi du temps créé avec succès');
                    }
                }
                window.closeModal();
            }
        }
    });

    document.body.addEventListener('htmx:afterRequest', function (evt) {
        // Suppression : si la réponse est vide, retirer la ligne
        if (evt.detail.xhr.response === '' && evt.detail.elt.closest('tr')) {
            let tr = evt.detail.elt.closest('tr');
            tr.remove();
            window.closeModal();
            window.showNotification('Suppression réussie', 'success');
        }
    });
});

 