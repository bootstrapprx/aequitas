import { useEffect, useState } from 'react';
import { apiInvoke } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

interface Phase {
    phase_id: string;
    title: string;
    status: string;
}

export default function Dashboard() {
    const [phases, setPhases] = useState<Phase[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchPhases = async () => {
            try {
                const data = await apiInvoke<Phase[]>('get_all_phases');
                setPhases(data);
            } catch (err: any) {
                setError(err.message || 'Failed to load phases');
            } finally {
                setLoading(false);
            }
        };

        fetchPhases();
    }, []);

    return (
        <div className="p-8 space-y-6">
            <h1 className="text-3xl font-bold">Metatheos Dashboard</h1>

            {loading && <p>Loading governance data...</p>}
            {error && <div className="text-red-500 p-4 border border-red-200 rounded">{error}</div>}

            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                {phases.map(phase => (
                    <Card key={phase.phase_id}>
                        <CardHeader>
                            <CardTitle>{phase.title}</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <p className="text-sm text-muted-foreground">{phase.status}</p>
                            <p className="text-xs font-mono mt-2">{phase.phase_id}</p>
                        </CardContent>
                    </Card>
                ))}
            </div>
        </div>
    );
}
