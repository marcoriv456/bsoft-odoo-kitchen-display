
/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import {
    Component,
    onWillStart,
    onMounted,
    onWillUnmount,
    useState,
} from "@odoo/owl";

const LABELS = {
    new: "Pendiente",
    preparing: "Preparando",
    ready: "Listo",
    served: "Entregado",
};

const NEXT = {
    new: "preparing",
    preparing: "ready",
    ready: "served",
};

const BUTTONS = {
    new: "Comenzar preparación",
    preparing: "Marcar listo",
    ready: "Marcar entregado",
};

export class BsoftKitchenDisplay extends Component {
    static template = "bsoft_kitchen_display.KitchenDisplay";

    setup() {
        this.notification = useService("notification");

        this.state = useState({
            lines: [],
            stations: [],
            stationId: "all",
            loading: true,
            error: "",
            now: Date.now(),
            updatingIds: [],
        });

        this.timer = null;
        this.clock = null;

        // null indica que todavía no se ha realizado la carga inicial.
        this.previous = null;

        this.loadingRequest = false;
        this.reloadPending = false;
        this.destroyed = false;

        onWillStart(async () => {
            await this.reload();
        });

        onMounted(() => {
            this.timer = setInterval(() => {
                void this.reload();
            }, 5000);

            this.clock = setInterval(() => {
                this.state.now = Date.now();
            }, 1000);
        });

        onWillUnmount(() => {
            this.destroyed = true;

            if (this.timer) {
                clearInterval(this.timer);
                this.timer = null;
            }

            if (this.clock) {
                clearInterval(this.clock);
                this.clock = null;
            }
        });
    }

    async rpc(route, params = {}) {
        const response = await fetch(route, {
            method: "POST",
            credentials: "same-origin",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                jsonrpc: "2.0",
                method: "call",
                params,
                id: Date.now(),
            }),
        });

        if (!response.ok) {
            throw new Error(`Error HTTP ${response.status}`);
        }

        const json = await response.json();

        if (json.error) {
            throw new Error(
                json.error.data?.message ||
                json.error.message ||
                "Error en la solicitud RPC"
            );
        }

        return json.result;
    }

    async reload() {
        if (this.destroyed) {
            return;
        }

        // Evitar solicitudes simultáneas sin perder la siguiente actualización.
        if (this.loadingRequest) {
            this.reloadPending = true;
            return;
        }

        this.loadingRequest = true;

        try {
            const stationId =
                this.state.stationId === "all"
                    ? false
                    : Number(this.state.stationId);

            const data = await this.rpc(
                "/bsoft_kitchen_display/data",
                { station_id: stationId }
            );

            if (this.destroyed) {
                return;
            }

            if (data?.error) {
                throw new Error(data.error);
            }

            const lines = data?.lines || [];
            const stations = data?.stations || [];

            const newIds = new Set(
                lines
                    .filter((line) => line.state === "new")
                    .map((line) => line.id)
            );

            // No emitir alertas durante la carga inicial.
            if (
                this.previous !== null &&
                [...newIds].some((id) => !this.previous.has(id))
            ) {
                this.playAlert();
            }

            this.previous = newIds;
            this.state.lines = lines;
            this.state.stations = stations;
            this.state.error = "";
        } catch (error) {
            if (!this.destroyed) {
                this.state.error =
                    error.message ||
                    "No se pudieron cargar los pedidos";
            }
        } finally {
            this.loadingRequest = false;

            if (!this.destroyed) {
                this.state.loading = false;

                if (this.reloadPending) {
                    this.reloadPending = false;
                    void this.reload();
                }
            }
        }
    }

    async changeState(line) {
        const nextState = NEXT[line.state];

        if (
            !nextState ||
            this.state.updatingIds.includes(line.id)
        ) {
            return;
        }

        this.state.updatingIds.push(line.id);

        try {
            const result = await this.rpc(
                "/bsoft_kitchen_display/set_state",
                {
                    line_id: line.id,
                    state: nextState,
                }
            );

            if (result?.error) {
                throw new Error(result.error);
            }

            this.notification.add(
                "Pedido actualizado correctamente",
                { type: "success" }
            );

            await this.reload();
        } catch (error) {
            console.error(
                "Error al cambiar el estado:",
                error
            );

            this.state.error =
                error.message ||
                "No se pudo actualizar el pedido";

            this.notification.add(this.state.error, {
                type: "danger",
            });
        } finally {
            this.state.updatingIds =
                this.state.updatingIds.filter(
                    (id) => id !== line.id
                );
        }
    }

    setStation(event) {
        this.state.stationId = event.target.value;
        void this.reload();
    }

    label(state) {
        return LABELS[state] || state;
    }

    button(state) {
        return BUTTONS[state] || "Cambiar estado";
    }

    isUpdating(line) {
        return this.state.updatingIds.includes(line.id);
    }

    getTimestamp(line) {
        const start = line.started_at || line.created_at;

        if (!start) {
            return null;
        }

        const normalized = start.includes("T")
            ? start
            : start.replace(" ", "T");

        // Las fechas de Odoo sin zona horaria normalmente están en UTC.
        const hasTimezone =
            /(?:Z|[+-]\d{2}:\d{2})$/i.test(normalized);

        const timestamp = new Date(
            hasTimezone ? normalized : `${normalized}Z`
        ).getTime();

        return Number.isNaN(timestamp) ? null : timestamp;
    }

    elapsed(line) {
        const timestamp = this.getTimestamp(line);

        if (timestamp === null) {
            return "—";
        }

        const minutes = Math.max(
            0,
            Math.floor(
                (this.state.now - timestamp) / 60000
            )
        );

        return `${minutes} min`;
    }

    ageClass(line) {
        const station = this.state.stations.find(
            (item) => item.id === line.station_id
        );

        const timestamp = this.getTimestamp(line);

        if (!station || timestamp === null) {
            return "";
        }

        const minutes =
            (this.state.now - timestamp) / 60000;

        if (
            station.critical != null &&
            minutes >= Number(station.critical)
        ) {
            return "critical";
        }

        if (
            station.warning != null &&
            minutes >= Number(station.warning)
        ) {
            return "warning";
        }

        return "";
    }

    playAlert() {
        try {
            const AudioContextClass =
                window.AudioContext ||
                window.webkitAudioContext;

            if (!AudioContextClass) {
                return;
            }

            const context = new AudioContextClass();
            const oscillator = context.createOscillator();
            const gain = context.createGain();

            oscillator.connect(gain);
            gain.connect(context.destination);

            oscillator.frequency.value = 880;
            gain.gain.value = 0.08;

            oscillator.start();
            oscillator.stop(context.currentTime + 0.18);

            oscillator.onended = () => {
                void context.close();
            };
        } catch (error) {
            // El navegador puede bloquear el audio
            // hasta que el usuario interactúe con la página.
        }
    }
}

registry.category("actions").add(
    "bsoft_kitchen_display",
    BsoftKitchenDisplay
);
